"""Level 188: the hotel's furniture, the courtyard's props, the windows into 188 in other levels, and the items.
Called from gen_188.py (see there for the conventions: everything modelled facing north, real 3D detail)."""
import os

from detail_kit import ground_storable
from gen_188_kit import (
    ASSETS, CERAMIC, CLOTH, GLASS, LANG, METAL, PARTS, SIDES, STONE, WOOD, WRITTEN,
    bx, bxa, bxf, cube, cyl, drops, mirror_x, reg, retex, shift, split, split_boxes, vblock, vx, write_json,
)

PLANK, CLOTHI = "game:plank-aged", "game:cloth-plain"
SHIRT, TROUSERS, BOOTS = "game:clothes-upperbody-commoner-shirt", "game:clothes-lowerbody-commoner-trousers", "game:clothes-foot-commoner-boots"
FURN = {"l188furniture": True}


def hung(els):
    return shift(els, dz=16)


def tall_split(els, part):
    from gen_188 import vsplit
    return vsplit(els, part)


# ======================================================================== Rooms

def bedroom():
    # ---- The double bed: two single halves, each a vanilla-style bed (BlockBed: -{head|feet}-{side}, side = head to
    # feet). Modelled with the feet toward north (z 0) and the head against the wall (z 16); the left half (of someone
    # lying in it: west, for side north) has its outer edge at x 0, meeting the right half at x 16.
    def bed(v):
        head = v["part"] == "head"
        els = [bx("Base", (0.4, 1.2, 0 if head else 0.6), (16, 6, 15.4 if head else 16), "upholstery"),
               bx("Mattress", (0.8, 6, 0 if head else 1), (16, 10, 15 if head else 16), "duvet")]
        if head:
            els += [bx("Leg", (1, 0, 13.4), (2.6, 1.2, 15), "black"),
                    bx("Duvet", (0.4, 10, 0), (16, 11, 8.6), "duvet"), bx("Fold", (0.4, 10.4, 7.4), (16, 11.8, 9.6), "duvet"),
                    bx("Drape", (0.1, 6.4, 0), (0.4, 11, 8.6), "duvet", faces=("west", "up", "north", "south")),
                    bx("Pillow", (2.2, 10, 10.2), (14.6, 12.6, 14.6), "pillow"), bx("Pillow2", (3, 12.6, 11), (13.8, 13.4, 13.8), "pillow")]
        else:
            els += [bx("Leg", (1, 0, 1), (2.6, 1.2, 2.6), "black"),
                    bx("Duvet", (0.4, 10, 0.6), (16, 11, 16), "duvet"),
                    bx("Drape", (0.1, 6.4, 0.6), (0.4, 11, 16), "duvet", faces=("west", "up", "north", "south")),
                    bx("DrapeF", (0.4, 6.4, 0.3), (16, 11, 0.6), "duvet", faces=("north", "up", "west")),
                    bx("Throw", (0.2, 11, 2.4), (16, 11.6, 7.4), "throw"),
                    bx("ThrowF", (0.2, 7.2, 0.1), (16, 11.6, 0.6), "throw", faces=("north", "up", "west", "east")),
                    bx("ThrowS", (-0.1, 7.6, 0.6), (0.2, 11.6, 7.4), "throw", faces=("west", "up", "north", "south"))]
        return els if v["lr"] == "l" else mirror_x(els)

    vblock("l188-bed", "Hotel Bed", [("lr", ["l", "r"]), ("part", ["head", "feet"]), ("side", SIDES)], bed,
           box=(0, 0, 0, 1, 0.6875, 1), material="Cloth", sounds=CLOTH, data={
               "class": "BackroomsBed", "entityClassByType": {"*-head-*": "BackroomsBed"}, "resistance": 2,
               "attributes": dict(FURN, sleepEfficiency=0.8, restQuality=1.0, bedFoot="side", bedDropHead=True, bedBreakPartner=True),
               "creativeinventory": {"general": ["l188-bed-l-head-north"], "backrooms": ["l188-bed-l-head-north"]}},
           comment="Level 188: half of a double bed (l/r: the half on the left/right of someone lying in it), a real bed (the mod's BackroomsBed, side = head toward feet): "
                   "grey upholstered base, white duvet, two pillows, a grey throw across the foot")

    # ---- Headboard (rel 4s+2 over the head tiles, wall-hung): grey fabric with real buttons; l/r as seen from in front
    def headboard(v):
        els = [bx("Panel", (0, -4, -2), (16, 8, 0), "headfabric")]
        outer = (14.6, 16) if v["lr"] == "l" else (0, 1.4)
        els.append(bx("Edge", (outer[0], -4.2, -2.3), (outer[1], 8.2, 0), "headfabric"))
        for r, y in enumerate((-1.5, 2, 5.5)):
            for c in range(4):
                x = 2 + c * 4 + (1 if r % 2 else 0)
                if 0 < x < 15:
                    els.append(bx(f"Btn{r}{c}", (x - 0.5, y - 0.5, -2.5), (x + 0.5, y + 0.5, -2), "button"))
        return hung(els)

    vblock("l188-headboard", "Headboard", [("lr", ["l", "r"]), ("side", SIDES)], headboard, collide=False,
           sel=lambda v: (0, 0, 0.85, 1, 0.5, 1), material="Cloth", sounds=CLOTH,
           data={"attributes": FURN, "drops": drops((CLOTHI, 1, 0.5))},
           comment="Level 188: half of a buttoned grey headboard, wall-hung over the bed's head (rel 4s+2, reaching down behind the pillows)")

    # ---- Nightstand with its lamp
    def nightstand(v):
        on = v["state"] == "on"
        els = [bx("Body", (3, 0, 5), (13, 9, 15), "oak"), bx("Drawer", (3.6, 5, 4.6), (12.4, 8.2, 5), "drawerfront"),
               bx("Knob", (7.4, 6.2, 4.1), (8.6, 7, 4.6), "chrome"), bx("Shelf", (3.6, 0.8, 4.8), (12.4, 1.4, 5), "oak"),
               bx("LampBase", (6.5, 9, 9.5), (9.5, 9.6, 12.5), "lampbase")]
        els += cyl("LampStem", 8, 11, 0.6, 9.6, 13, "lampbase")
        shade_t = "shade-on" if on else "shade-off"
        g = 200 if on else 0
        els += [bx("Shade", (5.5, 13, 8.5), (10.5, 17, 13.5), shade_t, glow=g)]
        return els

    vblock("l188-nightstand", "Nightstand", [("state", ["on", "off"]), ("side", SIDES)], nightstand, box=(0.18, 0, 0.3, 0.82, 0.56, 0.94),
           data={"attributes": FURN, "lightHsvByType": {"*-on-*": [7, 3, 10]}, "drops": drops((PLANK, 1, 0.5), ("block:game:candle", 0.2, 0))},
           comment="Level 188: a grey-oak nightstand with a drawer and a bedside lamp (on: light 10, warm)",
           names={"l188-nightstand-*": "Nightstand"})

    # ---- Wall desk on a single leg, a flatscreen TV on its foot
    def desk(v):
        return [bx("Top", (0, 10, 8), (16, 11, 16), "oak"), bx("Apron", (0.5, 8.4, 8.6), (15.5, 10, 15.6), "oak"),
                bx("Leg", (1.2, 0, 9), (2.8, 10, 10.6), "chrome"), bx("Foot", (0.8, 0, 8.6), (3.2, 0.4, 11), "chrome"),
                bx("Rail", (14.6, 8.4, 15), (16, 10, 16), "oak"),
                bx("TV", (2, 13.2, 13), (14, 20.2, 14), "black"), bxf("Screen", (2.4, 13.6, 12.95), (13.6, 19.8, 13), "screen-off", faces=("north",)),
                bx("TVNeck", (7.4, 11, 13.4), (8.6, 13.2, 14.2), "black"), bx("TVFoot", (5.5, 11, 12), (10.5, 11.4, 15), "black"),
                bx("Remote", (11, 11, 10), (12.2, 11.4, 13), "black")]

    vblock("l188-desk", "Desk", [("side", SIDES)], desk, box=(0, 0, 0.5, 1, 0.7, 1),
           data={"attributes": FURN, "drops": drops((PLANK, 2, 1), ("scrapwire", 0.5, 0.5))},
           comment="Level 188: a wall desk on a single leg, a dead flatscreen TV on its foot (its back against the wall)")

    def chair(v):
        els = []
        for i, (x, z) in enumerate(((3, 3), (11.8, 3), (3, 11.8), (11.8, 11.8))):
            els.append(bx(f"Leg{i}", (x, 0, z), (x + 1.2, 7.4, z + 1.2), "chrome"))
        els += [bx("Seat", (2.6, 7.4, 2.6), (13.4, 9.4, 13.4), "chairfabric"),
                bx("Back", (3, 9.4, 12), (13, 17.6, 13.6), "chairfabric"), bx("BackTop", (3.4, 17.6, 12.2), (12.6, 18.2, 13.4), "chairfabric")]
        return els

    vblock("l188-chair", "Desk Chair", [("side", SIDES)], chair, box=(0.15, 0, 0.15, 0.85, 0.6, 0.85),
           data={"attributes": FURN, "drops": drops(("game:stick", 1, 1), (CLOTHI, 0.3, 0.3))},
           comment="Level 188: a desk chair in charcoal fabric on chrome legs (the sitter faces the side)")

    def armchair(v):
        els = [bx("Base", (2, 0, 2.4), (14, 2, 14), "black"),
               bx("Seat", (2.6, 2, 2), (13.4, 7.6, 13.6), "teal"), bx("Cushion", (4, 7.6, 2.4), (12, 9, 11), "teal"),
               bx("Back", (2.2, 7.6, 11), (13.8, 15, 14.2), "teal"), bx("ArmL", (11.8, 7.6, 2.4), (14, 12, 12), "teal"),
               bx("ArmR", (2, 7.6, 2.4), (4.2, 12, 12), "teal"), bx("BackTop", (3, 15, 11.4), (13, 15.8, 13.8), "teal")]
        return els

    vblock("l188-armchair", "Armchair", [("side", SIDES)], armchair, box=(0.12, 0, 0.12, 0.88, 0.62, 0.9),
           data={"attributes": FURN, "drops": drops((CLOTHI, 1, 0.5), ("game:stick", 1, 0.5))},
           comment="Level 188: a squat teal tub armchair (the sitter faces the side)")

    # ---- Wardrobe: an open hanging niche two blocks tall: rail, hangers, two grey hotel robes, a shelf, an iron, a safe
    def wardrobe(v):
        els = [bx("Plinth", (1, 0, 8), (15, 1, 16), "oak"), bx("SideL", (14, 1, 7.6), (15.4, 32, 16), "oak"),
               bx("SideR", (0.6, 1, 7.6), (2, 32, 16), "oak"), bx("Top", (0.6, 30.6, 7.4), (15.4, 32, 16), "oak"),
               bx("Back", (2, 1, 15.4), (14, 30.6, 16), "wall-room", faces=("north",)), bx("Floor", (2, 1, 8), (14, 1.6, 15.4), "oak"),
               bx("Shelf", (2, 25.6, 8), (14, 26.4, 15.4), "oak"),
               bx("Safe", (8.4, 26.4, 10), (13.4, 30.4, 15.2), "safe"), bx("SafeKey", (9.2, 28, 9.6), (11.4, 29.4, 10), "reader"),
               bx("Iron", (3, 26.4, 11), (7, 28, 14), "iron-white"), bx("Rail", (2, 23.2, 11.4), (14, 24, 12.2), "chrome")]
        for i, (x, robe) in enumerate(((4.6, True), (8, True), (11.4, False))):
            els.append(bx(f"Hook{i}", (x - 0.2, 22.4, 11.6), (x + 0.2, 23.6, 12), "chrome"))
            els.append(bx(f"Hanger{i}", (x - 0.3, 21.8, 9), (x + 0.3, 22.4, 14.6), "chrome"))
            if robe:
                els += [bx(f"Robe{i}", (x - 0.9, 6, 9.2), (x + 0.9, 21.8, 14.4), "robe"),
                        bx(f"Shoulder{i}", (x - 1.1, 19, 8.6), (x + 1.1, 21.8, 15), "robe")]
        return tall_split(els, v["part"])

    vblock("l188-wardrobe", "Wardrobe", [("part", ["lower", "upper"]), ("side", SIDES)], wardrobe, box=(0.04, 0, 0.46, 0.96, 1, 1),
           data={"attributes": FURN, "dropsByType": {"*-lower-*": drops((CLOTHI, 1.5, 0.5), (SHIRT, 0.07, 0), (TROUSERS, 0.05, 0), (BOOTS, 0.03, 0)),
                                                     "*": drops((PLANK, 1, 0.5))}},
           comment="Level 188: an open hanging niche, two blocks tall: a rail, hangers, two grey hotel robes, a shelf with an iron and a safe. Breaks into cloth and now and then clothes")

    # ---- Minibar: a small black fridge with a glass door, bottles inside
    def minibar(v):
        return [bx("Body", (3, 0, 5), (13, 9, 15), "fridge"), bxf("Door", (3.2, 0.4, 4.7), (12.8, 8.6, 5), "minibar-door", faces=("north",)),
                bx("Handle", (11.4, 2, 4.2), (12, 7, 4.7), "chrome"), bx("Vent", (4, 0.2, 4.8), (12, 0.8, 5), "black", faces=("north",))]

    vblock("l188-minibar", "Minibar", [("side", SIDES)], minibar, box=(0.18, 0, 0.3, 0.82, 0.56, 0.94),
           data={"attributes": FURN, "drops": drops(("almondwater", 0.5, 0), ("l188-juicebox", 0.4, 0), ("crackers", 0.3, 0))},
           comment="Level 188: a small black fridge with a glass door, bottles inside. Breaks into Almond Water, juice and crackers, sometimes")

    def rack(v):
        els = []
        for i, (z1, z2, a) in enumerate(((5, 13, 1), (5, 13, -1))):
            for j, x in enumerate((3, 12)):
                els.append(bx(f"Leg{i}{j}", (x, 0, 8.6), (x + 1, 9.2, 9.4), "oak", rot=(30 * a, 0, 0), origin=(x + 0.5, 4.2, 9)))
        els += [bx("StrapA", (3, 8, 5.8), (13, 8.4, 6.8), "strap"), bx("StrapB", (3, 8, 9.2), (13, 8.4, 10.2), "strap"),
                bx("StrapC", (3, 8, 11.6), (13, 8.4, 12.6), "strap"), bx("RailL", (3, 7.4, 5), (4, 8.2, 13), "oak"), bx("RailR", (12, 7.4, 5), (13, 8.2, 13), "oak")]
        return els

    vblock("l188-luggagerack", "Luggage Rack", [("side", SIDES)], rack, box=(0.18, 0, 0.3, 0.82, 0.52, 0.82),
           data={"attributes": FURN, "drops": drops(("game:stick", 2, 1))}, comment="Level 188: a folding luggage rack with webbing straps")

    # ---- The bathroom pod's pieces, each with its frosted-glass panel(s), 2 blocks tall in one block
    def panel_x(x1, x2, name="Panel"):
        return [bxa(name, (x1, 0, 0), (x2, 32, 16), "frosted", faces=("east", "west")),
                bx(name + "Top", (x1 - 0.2, 31, 0), (x2 + 0.2, 32, 16), "frame-white"),
                bx(name + "Foot", (x1 - 0.2, 0, 0), (x2 + 0.2, 0.8, 16), "frame-white")]

    def panel_z(z1, z2, x1=0, x2=16, name="Front"):
        return [bxa(name, (x1, 0, z1), (x2, 32, z2), "frosted", faces=("north", "south")),
                bx(name + "Top", (x1, 31, z1 - 0.2), (x2, 32, z2 + 0.2), "frame-white"),
                bx(name + "Foot", (x1, 0, z1 - 0.2), (x2, 0.8, z2 + 0.2), "frame-white")]

    def shower(v):
        els = panel_x(0, 1)  # its right edge seen from the front (west, for side north)
        els += [bx("Tray", (1, 0, 0), (16, 1.2, 16), "porcelain"), bx("Drain", (7.4, 1.2, 9.4), (8.6, 1.3, 10.6), "chrome", faces=("up",)),
                bx("Rail", (7.6, 14, 15.2), (8.4, 30, 15.8), "chrome"), bx("Head", (6.6, 28, 12.6), (9.4, 28.6, 15.2), "chrome"),
                bx("Arm", (7.7, 28.6, 14.6), (8.3, 29.2, 15.8), "chrome"), bx("Mixer", (6.8, 16, 15), (9.2, 18.6, 16), "chrome"),
                bx("Screen", (1, 1.2, 0.4), (7, 30, 0.9), "frosted", faces=("north", "south"))]
        return els

    def poddoor(v):
        els = panel_x(0, 1) + panel_z(0, 0.8, 1, 8.6, "Fixed")
        els += [bxa("Slide", (6.6, 0.8, 1.0), (15.6, 31, 1.6), "frosted", faces=("north", "south")),
                bx("SlideEdge", (15.0, 0.8, 0.9), (15.8, 31, 1.7), "frame-white"),
                bx("Handle", (14, 13, 1.6), (14.6, 19, 2.4), "chrome"), bx("Track", (1, 31, 0), (16, 32, 2), "frame-white")]
        return els

    def sink(v):
        els = panel_z(0, 1)
        els += [bx("Basin", (3, 13, 1), (13, 15, 8), "porcelain"), bx("Bowl", (4, 14.6, 2), (12, 15.05, 7), "chrome", faces=("up",)),
                bx("Under", (4, 11, 1), (12, 13, 6), "porcelain"), bx("Tap", (7.4, 15, 1), (8.6, 18, 2.2), "chrome"),
                bx("Spout", (7.4, 17, 2.2), (8.6, 18, 4.6), "chrome"), bx("Mirror", (3.5, 19, 1), (12.5, 29, 1.3), "mirror", faces=("south",)),
                bx("MirrorRim", (3.2, 18.7, 1), (12.8, 29.3, 1.2), "frame-white", faces=("south",))]
        return els

    pod = {"blockmaterial": "Glass", "attributes": FURN, "drops": drops(("glassshard", 1, 0.5))}
    vblock("l188-shower", "Shower", [("side", SIDES)], shower, colboxes=lambda v: [(0, 0, 0, 1 / 16, 1.5, 1)], selboxes=lambda v: [(0, 0, 0, 1, 1, 1)],
           data=pod, material="Glass", sounds=GLASS, comment="Level 188: the bathroom pod's shower: a tray, a rail head, a mixer, and a frosted panel on its right edge (seen from its front)")
    vblock("l188-poddoor", "Bathroom Door", [("side", SIDES)], poddoor,
           colboxes=lambda v: [(0, 0, 0, 1 / 16, 1.5, 1), (0, 0, 0, 0.55, 1.5, 0.11)], selboxes=lambda v: [(0, 0, 0, 1, 1, 0.2), (0, 0, 0, 0.1, 1, 1)],
           data=pod, material="Glass", sounds=GLASS, comment="Level 188: the bathroom pod's way in: a frosted panel on its right edge, a sliding door half open on its front edge")
    vblock("l188-sink", "Basin", [("side", SIDES)], sink, colboxes=lambda v: [(0, 0, 0, 1, 1.5, 1 / 16), (3 / 16, 0.7, 0, 13 / 16, 0.95, 0.5)],
           selboxes=lambda v: [(0, 0, 0, 1, 1, 0.5)], data=pod, material="Glass", sounds=GLASS,
           comment="Level 188: the bathroom pod's basin, hung on the inside of the frosted panel along its front edge, a mirror above")


# ======================================================================== Service, lobby

def service():
    def cart(v):
        els = [bx("Frame", (1, 2, 4), (15, 14, 12), "cartgrey"), bx("Top", (0.6, 14, 3.6), (15.4, 14.8, 12.4), "cartgrey")]
        for i, (x, z) in enumerate(((1.5, 4.5), (13.5, 4.5), (1.5, 10.5), (13.5, 10.5))):
            els.append(bx(f"Wheel{i}", (x - 0.8, 0, z - 0.8), (x + 0.8, 2, z + 0.8), "rubber"))
        els += [bx("Towels", (2, 14.8, 5), (8, 17.4, 11), "towel"), bx("Towels2", (8.6, 14.8, 5.5), (13.6, 16.6, 10.5), "towel"),
                bx("Bag", (15, 3, 4.6), (17.4, 13, 11.4), "linenbag"), bx("Bottle1", (3, 9, 3.4), (4.4, 12.6, 4.8), "bottle-blue"),
                bx("Bottle2", (5, 9, 3.4), (6.4, 12, 4.8), "bottle-green"), bx("MopPole", (-0.6, 2, 7.4), (0.4, 24, 8.4), "chrome", rot=(0, 0, -6), origin=(0, 2, 8)),
                bx("Mop", (-1.6, 0.4, 6.4), (1.4, 3, 9.4), "mophead")]
        return els

    vblock("l188-housekeepingcart", "Housekeeping Cart", [("side", SIDES)], cart, box=(0.04, 0, 0.22, 1, 0.92, 0.78),
           material="Metal", sounds=METAL,
           data={"attributes": FURN, "drops": drops((CLOTHI, 3, 1), ("l188-keycard", 0.25, 0), ("block:game:candle", 0.4, 0.3))},
           comment="Level 188: a grey housekeeping cart, folded towels, a linen bag, bottles and a mop. Breaks into cloth, candles and now and then the housekeeping keycard")

    def shelf(v):
        els = []
        for i, (x, z) in enumerate(((0.5, 8.5), (14.5, 8.5), (0.5, 15), (14.5, 15))):
            els.append(bx(f"Post{i}", (x, 0, z), (x + 1, 16, z + 1), "steel"))
        for i, y in enumerate((1, 6, 11)):
            els.append(bx(f"Shelf{i}", (0.5, y, 8.5), (15.5, y + 0.6, 16), "steel"))
            els.append(bx(f"Sheets{i}", (2, y + 0.6, 9.4), (14, y + 3.6 - (i % 2) * 0.8, 15.4), "sheets"))
        els.append(bx("Top", (0.5, 15.4, 8.5), (15.5, 16, 16), "steel"))
        return els

    vblock("l188-linenshelf", "Linen Shelf", [("side", SIDES)], shelf, box=(0, 0, 0.5, 1, 1, 1), material="Metal", sounds=METAL,
           data={"attributes": FURN, "drops": drops((CLOTHI, 4.5, 1.5), ("metalbracket", 1, 0.5))},
           comment="Level 188: steel shelving stacked with folded sheets and towels (the laundry and linen stores)")


def lobby():
    def reception(v):
        end = v["kind"] == "end"
        els = [bx("Fascia", (0, 0, 3), (16, 14, 4), "fascia"), bx("Counter", (0, 14, 2.4), (16, 15, 8), "desktop"),
               bx("Strip", (0, 1, 2.6), (16, 2, 3), "backlit", glow=230, faces=("north", "down")),
               bx("Work", (0, 9, 4), (15.95 if end else 16, 10, 13), "desktop"), bx("Kick", (0, 0, 3.6), (16, 1, 13), "black", faces=("up",)),
               bx("Panel", (0, 1, 12), (16, 9, 13), "oak", faces=("north",))]
        if end:
            els += [bx("Return", (14.4, 0, 4), (16, 14, 13), "fascia"), bx("ReturnTop", (14, 14, 4), (16, 15, 13.6), "desktop"),
                    bx("StripE", (15.6, 1, 4), (16.05, 2, 13), "backlit", glow=230, faces=("east", "down"))]
        else:
            els += [bx("Bell", (11, 15, 4.6), (12.6, 16, 6.2), "chrome"), bx("Book", (3, 15, 3.6), (8, 15.6, 7), "upholstery")]
        return els

    vblock("l188-reception", "Reception Desk", [("kind", ["straight", "end"]), ("side", SIDES)], reception,
           boxes=lambda v: (0, 0, 0.15, 1, 0.94, 0.85),
           data=dict({"attributes": FURN, "lightHsv": [7, 2, 7], "drops": drops((PLANK, 2, 1), ("scrapwire", 0.5, 0.5))},
                     **({"behaviors": [{"name": "BackroomsL188GuestBook"}]} if reg("BackroomsL188GuestBook") else {})),
           comment="Level 188: the lobby's reception desk, a light wood fascia with a backlit strip (light 7); the clerk's side is behind (end: with a return on its east side). "
                   "The straight lengths have the guest book open on the counter: right-click reads it",
           names={"l188-reception-*": "Reception Desk"})

    def keyrack(v):
        els = [bx("Back", (0, 1, -0.4), (16, 13, 0), "pigeon"), bx("Top", (0, 12.4, -3), (16, 13, -0.4), "pigeon"),
               bx("Bottom", (0, 1, -3), (16, 1.6, -0.4), "pigeon"), bx("Mid1", (0, 4.8, -3), (16, 5.3, -0.4), "pigeon"),
               bx("Mid2", (0, 8.6, -3), (16, 9.1, -0.4), "pigeon")]
        for i, x in enumerate((0, 3.8, 7.75, 11.7, 15.5)):
            els.append(bx(f"Div{i}", (x, 1, -3), (x + 0.5, 13, -0.4), "pigeon"))
        for i, (x, y) in enumerate(((1.4, 2.0), (9.2, 5.8), (5.2, 9.6), (13.0, 2.0))):
            els.append(bx(f"Card{i}", (x, y, -1.4), (x + 1.8, y + 2.6, -1.1), "cardwhite"))
        return hung(els)

    vblock("l188-keyrack", "Key Rack", [("side", SIDES)], keyrack, collide=False, sel=lambda v: (0, 0.05, 0.8, 1, 0.82, 1),
           data={"attributes": FURN, "drops": drops((PLANK, 1, 0))},
           comment="Level 188: wall pigeonholes for room keys behind the reception desk, a few key cards still in them (wall-hung, rel 2)")

    def octagon(name, r, y1, y2, tex):
        """A round thing as an octagon: two crossed bars and a square."""
        return cyl(name, 8, 8, r, y1, y2, tex, k=0.414) + [bx(name + "c", (8 - 0.707 * r, y1, 8 - 0.707 * r), (8 + 0.707 * r, y2, 8 + 0.707 * r), tex)]

    def table(v):
        return octagon("Top", 6.6, 11.2, 12, "tabletop") + cyl("Column", 8, 8, 0.9, 1, 11.2, "chrome") + octagon("Foot", 4, 0, 1, "chrome")

    vblock("l188-roundtable", "Breakfast Table", [], table, rot=None, box=(0.12, 0, 0.12, 0.88, 0.75, 0.88),
           data={"attributes": FURN, "drops": drops((PLANK, 1, 0.5), ("metalbracket", 0.5, 0.5))},
           comment="Level 188: a round pedestal table in the breakfast area")
    LANG["block-l188-roundtable"] = "Breakfast Table"

    def lounge(v):
        return [bx("Base", (1.6, 0, 2), (14.4, 1.6, 14), "black"), bx("Seat", (1.6, 1.6, 1.6), (14.4, 6, 13), "loungefabric"),
                bx("Back", (1.6, 6, 11), (14.4, 12.4, 14.6), "loungefabric"), bx("ArmL", (12.6, 6, 2), (14.6, 9, 13), "loungefabric"),
                bx("ArmR", (1.4, 6, 2), (3.4, 9, 13), "loungefabric"), bx("Cushion", (3.4, 6, 2), (12.6, 7, 11), "loungefabric")]

    vblock("l188-loungechair", "Lounge Chair", [("side", SIDES)], lounge, box=(0.1, 0, 0.1, 0.9, 0.5, 0.9),
           data={"attributes": FURN, "drops": drops((CLOTHI, 1, 0.5))}, comment="Level 188: a low grey lounge chair in the lobby (the sitter faces the side)")

    # ---- Breakfast: a cereal dispenser of three gravity tubes (one portion each) and a juice dispenser with two drums
    def cereal(v):
        n = int(v["stage"])
        els = [bx("Stand", (1, 0, 6), (15, 7, 15), "oak"), bx("Back", (1, 7, 13.6), (15, 27, 15), "oak"),
               bx("Tray", (1.6, 7, 4), (14.4, 7.6, 9), "chrome")]
        for i, x in enumerate((4, 8, 12)):
            els += [bx(f"Cap{i}", (x - 1.8, 25, 8.2), (x + 1.8, 26.4, 11.8), "chrome"), bx(f"Base{i}", (x - 1.8, 11, 8.2), (x + 1.8, 12.4, 11.8), "chrome"),
                    bx(f"Knob{i}", (x - 0.8, 9, 7.4), (x + 0.8, 11, 9), "black"), bx(f"Spout{i}", (x - 0.7, 8.4, 9), (x + 0.7, 11, 10.4), "chrome")]
            if i < n:
                els.append(bx(f"Cereal{i}", (x - 1.5, 12.4, 8.5), (x + 1.5, 24.6, 11.5), "cereal"))
            els.append(bx(f"Tube{i}", (x - 1.6, 12.4, 8.4), (x + 1.6, 25, 8.5), "glass", faces=("north",)))
        return els

    def juice(v):
        n = int(v["stage"])
        els = [bx("Stand", (1, 0, 5), (15, 8, 15), "oak"), bx("Drip", (2, 8, 3.4), (14, 8.6, 8), "chrome")]
        for i, x in enumerate((4.6, 11.4)):
            top = 8.6 + 11.4 * n / 3  # the juice line in the drum
            if n:
                els.append(bx(f"Juice{i}", (x - 3, 8.6, 6.4), (x + 3, top, 12.4), "juice"))
            if n < 3:
                els.append(bx(f"Drum{i}", (x - 3, top, 6.4), (x + 3, 20, 12.4), "drumclear"))
            els += [bx(f"Lid{i}", (x - 3.2, 20, 6.2), (x + 3.2, 21, 12.6), "chrome"), bx(f"Tap{i}", (x - 0.6, 10, 5.2), (x + 0.6, 11.6, 6.4), "black")]
        return els

    disp = {"attributes": FURN, "drops": drops((PLANK, 1, 0.5))}
    if reg("BackroomsL188Dispenser"):
        disp["class"] = "BackroomsL188Dispenser"
    vblock("l188-cerealdispenser", "Cereal Dispenser", [("stage", ["3", "2", "1", "0"]), ("side", SIDES)], cereal, box=(0.06, 0, 0.25, 0.94, 1, 0.94),
           data=dict(disp, renderpass="Transparent"), comment="Level 188: three gravity tubes of breakfast cereal on a stand (the stage counts the tubes still full; 0 is empty)")
    vblock("l188-juicedispenser", "Juice Dispenser", [("stage", ["3", "2", "1", "0"]), ("side", SIDES)], juice, box=(0.06, 0, 0.3, 0.94, 0.8, 0.94),
           data=disp, comment="Level 188: a juice dispenser with two drums of something orange (the stage is how full they are; 0 is empty)")


# ======================================================================== The courtyard's props

import gen_188_b16  # noqa: E402  (graphics pass B16)

B16_COURTYARD = True  # (B16) the bollard, the downpipe and its hopper modelled (False: B0's boxes)


def courtyard():
    def downpipe(v):
        if B16_COURTYARD:
            return hung(gen_188_b16.downpipe())
        return hung([bx("Pipe", (6.5, 0, -4), (9.5, 16, -1), "downpipe"), bx("Bracket", (6, 8, -4.4), (10, 9.2, 0), "bracket"),
                     bx("Joint", (6.2, 13.6, -4.3), (9.8, 15, -0.7), "downpipe")])

    vblock("l188-downpipe", "Downpipe", [("side", SIDES)], downpipe, collide=False, sel=lambda v: (0.38, 0, 0.72, 0.62, 1, 1),
           data={"attributes": {"l188structure": True}, "drops": [], "resistance": 6, "sounds": dict(METAL)},
           material="Metal", sounds=METAL, comment="Level 188: a grey downpipe with brackets on the north façade (rel 2-20, wall-hung in the courtyard cell)")

    def downpipe_top(v):
        # Its head under the parapet's drip (rel 21): the pipe up into a hopper that takes the roof's water
        if B16_COURTYARD:
            return hung(gen_188_b16.downpipe_top())
        return hung([bx("Pipe", (6.5, 0, -4), (9.5, 10.5, -1), "downpipe"), bx("Hopper", (5, 10.5, -5.5), (11, 13.4, -1), "downpipe"),
                     bx("Lip", (4.6, 12.8, -5.9), (11.4, 13.4, -1), "downpipe"), bx("Bracket", (6, 5, -4.4), (10, 6.2, 0), "bracket")])

    vblock("l188-downpipetop", "Downpipe", [("side", SIDES)], downpipe_top, collide=False, sel=lambda v: (0.3, 0, 0.62, 0.7, 0.85, 1),
           data={"attributes": {"l188structure": True}, "drops": [], "resistance": 6, "sounds": dict(METAL)},
           material="Metal", sounds=METAL, comment="Level 188: the downpipe's hopper head under the parapet's drip (rel 21, wall-hung in the courtyard cell)")

    def drain(v):
        # the downpipe's shoe at the wall (north edge), its outlet over a grate in a dark puddle
        return [bx("PipeEnd", (6.5, 4, 12), (9.5, 16, 15), "downpipe"), bx("Shoe", (6.5, 2, 9.4), (9.5, 4.6, 15), "downpipe"),
                bx("Grate", (5, 0, 5), (11, 0.3, 11), "grate", faces=("up",)), bx("Frame", (4.6, 0, 4.6), (11.4, 0.2, 11.4), "drain", faces=("up",)),
                bx("Puddle", (2, 0, 2), (14, 0.08, 14), "puddle", faces=("up",)), bx("Puddle2", (4, 0, 0.5), (12, 0.06, 2), "puddle", faces=("up",))]

    d = drain(None)
    for e in d:
        if e["name"] in ("PipeEnd", "Shoe"):
            pass
    # the drain is placed only at the foot of the downpipe on the north façade: the wall lies to its north
    d = [dict(e, **{"from": [e["from"][0], e["from"][1], 16 - e["to"][2]], "to": [e["to"][0], e["to"][1], 16 - e["from"][2]],
                    "faces": {{"north": "south", "south": "north"}.get(k, k): fv for k, fv in e["faces"].items()}}) for e in d]
    sounds = dict(STONE, ambient="backrooms:ambient/188/pipe", ambientBlockCount=1)
    vblock("l188-drain", "Drain", [], lambda v: d, rot=None, collide=False, sel=lambda v: (0.25, 0, 0, 0.75, 0.3, 0.75),
           data={"attributes": {"l188structure": True}, "drops": [], "resistance": 6}, material="Metal", sounds=sounds,
           comment="Level 188: the downpipe's foot (rel 1, the façade to its north): the shoe running dark water into a grate in a puddle. It carries the pipe's sound")
    LANG["block-l188-drain"] = "Drain"

    def bollard(v):
        if B16_COURTYARD:
            return gen_188_b16.bollard(cyl("Band", 8, 8, 2.05, 6, 9, "bollardlight", glow=220, k=0.6))
        return (cyl("Body", 8, 8, 2, 0, 6, "bollard", k=0.6) + cyl("Band", 8, 8, 2.05, 6, 9, "bollardlight", glow=220, k=0.6)
                + cyl("Cap", 8, 8, 2.1, 9, 10, "bollard", k=0.6))

    vblock("l188-bollard", "Bollard Lamp", [], bollard, rot=None, box=(0.36, 0, 0.36, 0.64, 0.625, 0.64),
           data={"attributes": {"l188structure": True}, "lightHsv": [8, 2, 10], "drops": [], "resistance": 6}, material="Metal", sounds=METAL,
           comment="Level 188: a squat dark bollard with a dim light band (light 10), one at each of the deck's diagonals")
    LANG["block-l188-bollard"] = "Bollard Lamp"

    def bench(v):
        els = [bx("LegL", (12, 0, 4), (14, 6, 12), "concrete-leg"), bx("LegR", (2, 0, 4), (4, 6, 12), "concrete-leg")]
        for i, z in enumerate((3.6, 6.0, 8.4, 10.8)):
            els.append(bx(f"Slat{i}", (0, 6, z), (16, 7.2, z + 2), "benchwood"))
        return els

    vblock("l188-bench", "Bench", [("side", SIDES)], bench, box=(0, 0, 0.2, 1, 0.45, 0.8),
           data={"attributes": {"l188structure": True}, "drops": drops((PLANK, 1, 0.5)), "resistance": 4},
           comment="Level 188: a slatted timber bench on concrete legs at the lawn's edge, facing the deck (the sitter faces the side)")

    def vent(v):
        return (cyl("Stack", 8, 8, 2.4, 0, 12, "vent") + [bx("Cowl", (4.6, 12, 4.6), (11.4, 13, 11.4), "vent"),
                bx("CowlTop", (5, 14.4, 5), (11, 15.4, 11), "vent"), bx("Post1", (5.4, 13, 7.4), (6.2, 14.4, 8.6), "vent"),
                bx("Post2", (9.8, 13, 7.4), (10.6, 14.4, 8.6), "vent"), bx("Base", (4, 0, 4), (12, 1, 12), "roof")])

    vblock("l188-ventstack", "Vent Stack", [], vent, rot=None, box=(0.28, 0, 0.28, 0.72, 0.96, 0.72),
           data={"attributes": {"l188structure": True}, "drops": [], "resistance": 6}, material="Metal", sounds=METAL,
           comment="Level 188: a vent stack with a cowl on the roof")
    LANG["block-l188-ventstack"] = "Vent Stack"


# ======================================================================== The windows into 188, in other levels

HOSTS = {
    # frame texture, sill texture, host wall (for the sill block)
    "l0": ("woodwhite", "woodwhite", "backrooms:block/wallpaper/chevron-plain"),
    "l1": ("alu", "sillstone", "backrooms:block/level1/concretewall-plain"),
    "fun": ("sash", "sash", "backrooms:block/fun/paint-orange"),
}


def entry_windows():
    """A 2 x 2 window with no glass, a blind half up, and behind it 188's courtyard at night (a lit peep-box: dark moss,
    the deck's edge, the opposite façade with three lit windows, two of them in real voxel frames)."""
    def window(v):
        host, part = v["host"], v["part"]
        ftex, stex, _ = HOSTS[host]
        from gen_188 import frame_composite, FRAME_BOXES  # noqa: F401
        els = frame_composite(tex=ftex, z=(0, 3))
        els += [bxa("Back", (0, 0, 15), (32, 32, 15.5), "x", faces=("north",), glow=70),
                bx("Floor", (0, 0, 3), (32, 1.5, 15), "sc-grassnight", faces=("up",), glow=40),
                bx("Ceil", (0, 30.5, 3), (32, 32, 15), "sc-courtnight", faces=("down",)),
                bx("SideR", (0, 0, 3), (1.5, 32, 15), "sc-courtnight", faces=("east",), glow=30),
                bx("SideL", (30.5, 0, 3), (32, 32, 15), "sc-courtnight", faces=("west",), glow=30)]
        # two of the lit windows across the courtyard, in real frames proud of the painting
        for i, (a, b, y1, y2) in enumerate(((5.75, 8.0, 24.75, 27.0), (23.75, 26.0, 20.5, 22.75))):
            x1, x2 = vx(a, b)
            els += [bx(f"W{i}T", (x1 - 0.4, y2, 14.2), (x2 + 0.4, y2 + 0.4, 15), "sc-courtnight", glow=30),
                    bx(f"W{i}B", (x1 - 0.4, y1 - 0.4, 14.2), (x2 + 0.4, y1, 15), "sc-courtnight", glow=30),
                    bx(f"W{i}L", (x2, y1, 14.2), (x2 + 0.4, y2, 15), "sc-courtnight", glow=30),
                    bx(f"W{i}R", (x1 - 0.4, y1, 14.2), (x1, y2, 15), "sc-courtnight", glow=30)]
        # the blind, half up: down over the top third, its roll and bar
        els += [bx("Roll", (1, 29.4, 3), (31, 31.4, 5), "roll"), bxa("Blind", (1.5, 21, 3.4), (30.5, 29.4, 3.9), "blind", faces=("north", "south")),
                bx("Bar", (1.5, 20.2, 3.2), (30.5, 21, 4.1), ftex if ftex != "woodwhite" else "alu"),
                bx("Cord", (2.6, 12, 2.6), (2.9, 29.4, 2.9), "cord")]
        if host == "fun":
            els += [bx("Balloon", (24, 12.6, 6), (28.6, 18, 10.6), "balloon-red"), bx("Knot", (25.9, 11.8, 7.9), (26.7, 12.6, 8.7), "balloon-red"),
                    bx("String", (26.2, 1.5, 8.2), (26.4, 11.8, 8.4), "string")]
        out = split(els, part)
        for e in out:
            if e["name"] == "Back":
                e["faces"]["north"]["texture"] = f"#courtview-{part}"
                e["faces"]["north"]["uv"] = [0, 0, 16, 16]
        return out

    from gen_188 import FRAME_BOXES
    boxes = [(x1, y1, 0, x2, y2, 3) for (x1, y1, _, x2, y2, _) in FRAME_BOXES]
    vblock("l188-entrywindow", "Window", [("host", list(HOSTS)), ("part", list(PARTS)), ("side", SIDES)], window,
           colboxes=lambda v: split_boxes(boxes, v["part"]), selboxes=lambda v: [(0, 0, 0, 1, 1, 1)],
           data={"drops": [], "resistance": 999, "lightHsv": [24, 3, 4], "lightAbsorption": 0, "attributes": {"l188structure": True}},
           material="Glass", sounds=GLASS,
           comment="Level 188's way in from Level 0, Level 1 and Level Fun: a window where no window should be, no glass, a blind half up, a dark courtyard and lit windows beyond "
                   "(side = the face toward the room you stand in; parts seen from there). No collision in the opening: you climb in from the sill")

    def sill(v):
        host = v["host"]
        ftex, stex, wall = HOSTS[host]
        els = [cube(wall), bx("Sill", (-0.4, 14, -2.4), (16.4, 16.03, 2), stex, faces=("north", "up", "down", "east", "west")),
               bx("Apron", (0, 12.4, -1), (16, 14, 0), stex, faces=("north", "down", "east", "west"))]
        if host == "fun":
            els.append(bxf("Confetti", (0, 16.02, -2.2), (16, 16.08, 2), "confetti", faces=("up",)))
        return els

    vblock("l188-entrysill", "Window Sill", [("host", list(HOSTS)), ("side", SIDES)], sill, box=(0, 0, 0, 1, 1, 1),
           data={"sidesolid": {"all": True}, "sideopaque": {"all": True}, "lightAbsorption": 99, "drops": [], "resistance": 999,
                 "attributes": {"l188structure": True}}, material="Stone", sounds=STONE,
           comment="Level 188: the sill under a window into 188 (rel 1), in the host's own wall: white wood in yellow wallpaper (l0), concrete (l1), a white sash sill with confetti (fun)")


# ======================================================================== Items

SPRITE_TRANSFORMS = {
    "guiTransform": {"rotation": {"x": 0, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0.5, "z": 0.5}, "scale": 1},
    "tpHandTransform": {"translation": {"x": -0.75, "y": -0.4, "z": -0.55}, "rotation": {"x": 0, "y": -45, "z": -10}, "scale": 0.6},
    "groundTransform": {"rotation": {"x": 90, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 2},
}


def items():
    folder = os.path.join(ASSETS, "itemtypes", "188")

    def item(code, english, desc, data):
        d = {"code": code, "texture": {"base": f"backrooms:item/188/{code[5:]}"},
             "creativeinventory": {"general": ["*"], "items": ["*"], "backrooms": ["*"]}, "materialDensity": 600}
        d.update(SPRITE_TRANSFORMS)
        d.update(data)
        write_json(os.path.join(folder, code + ".json"), ground_storable(d), english)
        WRITTEN["itemtypes"].append(code)
        LANG[f"item-{code}"] = english
        LANG[f"itemdesc-{code}"] = desc

    item("l188-keycard", "Housekeeping Keycard", "A white plastic master card with a grey stripe. HOUSEKEEPING. It opens the guest rooms that are only locked; it does nothing to a door that is held shut.",
         {"maxstacksize": 1, "attributes": {"l188keycard": True}})
    item("l188-cereal", "Breakfast Cereal", "Stale, but it is cereal.",
         {"maxstacksize": 16, "nutritionProps": {"satiety": 180, "foodcategory": "Grain"}})
    item("l188-juicebox", "Juice Box", "A little carton of orange something, still cold.",
         {"maxstacksize": 16, "nutritionProps": {"satiety": 120, "foodcategory": "Fruit"},
          "class": "BackroomsAlmondWater", "attributes": {"stabilityRestored": 0, "wardsDullers": False, "hydration": 350}})


def generate():
    bedroom()
    service()
    lobby()
    courtyard()
    entry_windows()
    items()
