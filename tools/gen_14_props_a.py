"""Level 14 "The Hospital": the models of the reception rooms and the inpatient wards (tools/gen_14_props.py).
Each function returns a list of elements modelled facing north (front toward -Z); texture keys are p-* files in
textures/block/14/ (tools/gen_14_props_tex.py)."""
import math

import modelkit as MK
from gen_14_props_kit import B, no, pic, glow, turned, transparent, rename, octagon, octagon_x, octagon_z, arc, rod, mirror_x, \
    move, turn, clip_z

VENEER = {"front": "p-veneer", "back": "p-veneer-side", "side": "p-veneer-side", "top": "p-veneer-side", "bottom": "p-veneer-side"}
WORK = {"top": "p-worktop", "side": "p-teal", "bottom": "p-veneer-side"}
LEDGE = {"top": "p-worktop", "side": "p-teal", "bottom": "p-veneer-side"}
VINYL = {"top": "p-vinyl", "front": "p-vinyl", "side": "p-vinyl-side", "back": "p-vinyl-side", "bottom": "p-vinyl-side"}


def castor(name, x, z, y=0.0, tex="p-darksteel", wheel="p-black"):
    """A swivel castor under a leg at (x, z): a fork plate and a wheel along x."""
    return [B(name + "Plate", (x - 0.75, y + 1.75, z - 0.75), (x + 0.75, y + 2.25, z + 0.75), tex),
            B(name + "Fork", (x - 0.5, y + 0.75, z - 0.25), (x + 0.5, y + 1.75, z + 0.75), tex, faces=no("down")),
            B(name + "Wheel", (x - 0.35, y, z - 0.6), (x + 0.35, y + 1.25, z + 0.85), wheel)]


# ======================================================================== Reception desk

def desk_mid(kind):
    """A straight tile of the oval reception desk: a veneered front panel (north) on a black kick, a teal band, a
    raised transaction ledge along the front, and behind it the receptionist's work surface over a drawer pedestal."""
    els = [
        B("Kick", (0, 0, 1.5), (16, 1.5, 3), "p-black", faces=("north", "up")),
        B("Fascia", (0, 1.5, 1), (16, 16, 3), VENEER, faces=no("east", "west", "down")),
        B("Band", (0, 9.5, 0.75), (16, 10.75, 1), "p-teal", faces=("north", "up", "down")),
        B("Ledge", (0, 16, 0.25), (16, 17.25, 6.5), LEDGE, faces=no("east", "west")),
        B("Work", (0, 11, 3), (16, 12, 12), WORK, faces=no("east", "west")),
        B("Pedestal", (10.5, 0, 4), (15.5, 11, 11.5), "p-veneer-side", faces=("south", "east", "west")),
    ]
    for i, x in enumerate((3.5, 12.5)):
        els.append(B(f"Bracket{i}", (x - 0.5, 13, 3), (x + 0.5, 16, 6), "p-steel", faces=no("up", "north")))
    for i, (y1, y2) in enumerate(((0.75, 4), (4.25, 7.5), (7.75, 10.5))):
        els += [B(f"Drawer{i}", (10.75, y1, 11.5), (15.25, y2, 11.9), "p-veneer", faces=no("north")),
                B(f"Pull{i}", (12, y2 - 1.1, 11.9), (14, y2 - 0.6, 12.4), "p-chrome", faces=no("north"))]
    if kind == "supplies":
        # rolled bandages, pill bottles, a box of antibiotics and a gauze pack, as left at the front desk
        els += octagon_x("RollA", 0, 13.25, 5, 1.25, 2.5, 5.5, "p-bandage")
        els += octagon_x("RollB", 0, 13.25, 7.75, 1.25, 3, 6, "p-bandage")
        els += turned(rod("RollC", "x", 14.4, 6.4, 1.1, 3.5, 6, "p-bandage"), ry=20, origin=(4.5, 14, 6.4))
        for i, (x, z) in enumerate(((8, 4.5), (9.6, 5.2), (8.6, 6.8))):
            els += [B(f"Pill{i}", (x - 0.75, 12, z - 0.75), (x + 0.75, 14.5, z + 0.75), {"side": "p-pillbottle", "top": "p-white"}),
                    B(f"PillCap{i}", (x - 0.85, 14.5, z - 0.85), (x + 0.85, 15.25, z + 0.85), "p-white")]
        els += turned([B("PillTipped", (11, 12, 8), (13.5, 13.5, 9.5), {"side": "p-pillbottle", "top": "p-white"})], ry=-25, origin=(12, 12, 8.7))
        els.append(pic(B("Box", (11.5, 12, 4), (15, 14.5, 7), {"all": "p-white"}), "north", "p-pillbox"))
        els[-1]["faces"]["up"] = {"texture": "#p-pillbox", "uv": [0, 0, 16, 9]}
        els.append(B("Gauze", (2, 12, 9), (6.5, 12.6, 11.5), "p-gauze"))
    elif kind == "lamp":
        # a desk lamp, its shade lit; and the sign-in book open on the ledge
        els += octagon("LampBase", 4.5, 8, 2, 12, 12.75, "p-brass")
        els.append(B("LampStem", (4.1, 12.75, 7.6), (4.9, 18, 8.4), "p-brass"))
        els.append(B("LampArm", (4.1, 17.5, 5.5), (4.9, 18.25, 8.4), "p-brass"))
        els += turned([B("LampShade", (2.25, 16, 3.25), (6.75, 18.5, 7), {"all": "p-shadelit"}, glow=200),
                       B("LampBulb", (3.5, 15.5, 4.25), (5.5, 16, 6), "p-bulb", glow=255)], rx=-12, origin=(4.5, 18, 5.5))
        els.append(pic(B("Ledger", (7.5, 17.25, 1.5), (14, 17.5, 5.5), "p-papers", faces=no("down")), "up", "p-ledger"))
        els.append(B("Pen", (14.2, 17.25, 2.5), (14.6, 17.6, 5.5), "p-black"))
    elif kind == "phone":
        # a beige desk phone, its handset in the cradle and a coiled cord; a heap of papers and a clipboard
        els += [B("Phone", (2.5, 12, 4.5), (8, 13.5, 9), {"all": "p-beige", "side": "p-beige-side"}),
                pic(B("Keys", (3.25, 13.5, 6.25), (6.25, 13.75, 8.75), "p-beige-side", faces=no("down")), "up", "p-phonepad"),
                B("Handset", (2.25, 13.75, 4.75), (8.25, 14.75, 5.9), {"all": "p-beige", "side": "p-beige-side"}),
                B("EarL", (2.25, 13.5, 4.5), (3.5, 14.75, 6.25), "p-beige-side"),
                B("EarR", (7, 13.5, 4.5), (8.25, 14.75, 6.25), "p-beige-side"),
                B("Cord", (1.5, 12, 5), (2.25, 12.75, 9.5), "p-beige-side")]
        els += turned([pic(B("PaperA", (9, 12, 3.5), (13.5, 12.25, 9.5), "p-papers", faces=no("down")), "up", "p-papers")], ry=8, origin=(11, 12, 6))
        els += turned([pic(B("PaperB", (9.5, 12.25, 4), (14, 12.5, 10), "p-papers", faces=no("down")), "up", "p-brochure")], ry=-14, origin=(11.5, 12, 7))
        els += [B("Clip", (9.5, 17.25, 1.5), (13.5, 17.5, 5.5), "p-veneer-side", faces=no("down")),
                pic(B("ClipSheet", (9.75, 17.5, 2.25), (13.25, 17.6, 5.25), "p-papers", faces=no("down")), "up", "p-chart"),
                B("ClipJaw", (10.75, 17.5, 1.6), (12.25, 17.9, 2.25), "p-chrome")]
    else:
        els += turned([pic(B("Sheet", (3, 12, 4), (7.5, 12.2, 10), "p-papers", faces=no("down")), "up", "p-papers")], ry=6, origin=(5, 12, 7))
        els.append(B("Mug", (7.5, 12, 8), (9, 13.75, 9.5), {"side": "p-white", "top": "p-black"}))
    return els


def desk_endl():
    """The west end of the oval desk: the front sweeps round in a quarter circle from the north edge to the south edge,
    closing the oval round the receptionist's side (centre of the curve at the block's south-east corner)."""
    c = (16, 16)
    els = []
    els += rename(arc("", *c, 13, 14.5, 0, 1.5, 0, 90, 8, "p-black", faces=("north", "up", "west", "east")), "Kick")
    els += rename(arc("", *c, 13, 15, 1.5, 16, 0, 90, 8, VENEER, faces=no("down")), "Fascia")
    els += rename(arc("", *c, 15, 15.25, 9.5, 10.75, 0, 90, 8, "p-teal", faces=("north", "up", "down")), "Band")
    els += rename(arc("", *c, 9.5, 15.75, 16, 17.25, 0, 90, 8, LEDGE), "Ledge")
    els += rename(arc("", *c, 4, 13, 11, 12, 0, 90, 8, WORK, faces=no("east", "west")), "Work")
    # two legs under the curve of the work surface, and brackets under the ledge
    for i, a in enumerate((30, 62)):
        r = 6.5
        x, z = 16 - r * math.sin(math.radians(a)), 16 - r * math.cos(math.radians(a))
        els.append(B(f"Leg{i}", (x - 0.6, 0, z - 0.6), (x + 0.6, 11, z + 0.6), "p-steel", faces=no("up", "down")))
        els.append(B(f"Foot{i}", (x - 1, 0, z - 1), (x + 1, 0.4, z + 1), "p-darksteel", faces=no("down")))
    # the sign-in clipboard on the ledge's curve, an old dried-up plant pot at the end
    els += turned([pic(B("Leaflet", (5.5, 17.25, 3), (9.5, 17.45, 6.5), "p-papers", faces=no("down")), "up", "p-brochure")],
                  ry=35, origin=(7.5, 17.25, 4.75))
    els += octagon("Pot", 9, 9.5, 1.6, 12, 14.5, "p-white")
    els += [B("Soil", (7.75, 14.2, 8.25), (10.25, 14.45, 10.75), "p-mould", faces=("up",)),
            B("Stalk", (8.8, 14.4, 9.3), (9.2, 17, 9.7), "p-vinemat", faces=no("up", "down"))]
    return els


def desk(part):
    if part == "endl":
        return desk_endl()
    if part == "endr":
        return mirror_x(desk_endl())
    return desk_mid(part)


# ======================================================================== Waiting chairs, floor lamp, table, bottles

def soda_bottle(name, x, z, y=0.0, tex="p-bottlegreen", label="p-sodalabel", r=1.15, h=5.5):
    """A soft-drink bottle standing at (x, z): body, label, shoulder, neck and a cap."""
    els = octagon(name + "Body", x, z, r, y, y + h, {"side": tex, "top": tex, "bottom": tex})
    els += octagon(name + "Label", x, z, r + 0.08, y + h * 0.25, y + h * 0.65, {"side": label, "top": tex}, faces=("north", "south", "east", "west"))
    els += octagon(name + "Neck", x, z, r * 0.55, y + h, y + h + 2, tex)
    els.append(B(name + "Cap", (x - 0.55, y + h + 2, z - 0.55), (x + 0.55, y + h + 2.6, z + 0.55), "p-cap"))
    return els


def soda_lying(name, x1, x2, cy, z, tex="p-bottlegreen", label="p-sodalabel2", r=1.15):
    els = rod(name + "Body", "x", cy, z, r, x1, x2, tex)
    els += rod(name + "Label", "x", cy, z, r + 0.08, x1 + 1.2, x2 - 1.2, label, faces=("north", "south", "up", "down"))
    els += rod(name + "Neck", "x", cy, z, r * 0.55, x2, x2 + 2, tex)
    els += rod(name + "Cap", "x", cy, z, r * 0.6, x2 + 2, x2 + 2.5, "p-cap")
    return els


def waitchair(kind):
    """A waiting-room seat facing north, one a block: teal vinyl on a dark steel shell, on a beam shared along the row,
    an armrest at each side (where two seats meet their arms read as one)."""
    seat = "p-vinyltorn" if kind == "torn" else "p-vinyl"
    up = dict(VINYL, top=seat)
    els = [
        B("Beam", (0, 3, 8), (16, 4.5, 10.5), "p-darksteel"),
        B("Post", (7.25, 0.5, 8.5), (8.75, 3, 10), "p-darksteel", faces=no("up", "down")),
        B("Foot", (6, 0, 5), (10, 0.5, 13.5), "p-darksteel", faces=no("down")),
        B("Bracket", (7, 4.5, 4.5), (9, 5.5, 12), "p-steel", faces=no("up")),
        B("Shell", (1.25, 5.5, 2.5), (14.75, 6.25, 12.5), "p-darksteel", faces=no("up")),
        B("Cushion", (1.25, 6.25, 2.25), (14.75, 8.25, 12.25), up, faces=no("down")),
        B("Roll", (1.25, 6, 1.75), (14.75, 8, 2.25), VINYL, faces=no("south")),
        B("Spine", (7, 5.5, 12.5), (9, 9.5, 13.5), "p-steel", faces=no("up", "down")),
    ]
    back = [B("BackShell", (1.25, 8.5, 12.5), (14.75, 19, 13.5), "p-darksteel"),
            B("BackCushion", (1.25, 9, 11.25), (14.75, 18.5, 12.5), dict(VINYL, front=("p-vinyltorn" if kind == "torn" else "p-vinyl")),
              faces=no("south"))]
    els += turned(back, rx=8, origin=(8, 8.5, 12.5))
    for s, x in (("W", 0.0), ("E", 15.25)):
        els += [B(f"ArmPost{s}", (x, 4.5, 8.25), (x + 0.75, 12, 9.25), "p-steel", faces=no("up", "down")),
                B(f"ArmBar{s}", (x, 11.25, 4), (x + 0.75, 12, 8.25), "p-steel", faces=no("up", "south")),
                B(f"ArmPad{s}", (x - 0.0, 12, 3), (x + 0.75, 13, 11), "p-black")]
    if kind == "magazine":
        els += turned([pic(B("MagA", (3, 8.25, 3.5), (9.5, 8.5, 11.5), "p-papers", faces=no("down")), "up", "p-magazine")],
                      ry=-14, origin=(6, 8.25, 7.5))
        els += turned([pic(B("MagB", (6, 8.5, 5), (11, 8.75, 10), "p-papers", faces=no("down")), "up", "p-brochure")],
                      rz=-6, origin=(8, 8.5, 7.5))
        els += turned([B("MagFold", (9, 8.4, 6), (12.5, 9.75, 6.25), "p-papers")], rx=-30, origin=(10.5, 8.4, 6.1))
    elif kind == "soda":
        els += soda_bottle("Soda", 5, 7, 8.25, "p-bottlestale")
        els += turned(soda_lying("Tipped", 8, 13, 9.4, 6, "p-bottlebrown"), ry=-20, origin=(10.5, 9.4, 6))
    elif kind == "torn":
        els += [B("FoamA", (5, 8.25, 6.5), (7, 8.75, 8), "p-foam"),
                B("FoamB", (12, 8.25, 3), (13, 8.6, 4), "p-foam"),
                B("FoamC", (3.5, 0, 2), (5, 0.6, 3), "p-foam")]
    return els


def floorlamp(part, on):
    """A standard lamp with a fabric shade. lower: a weighted base and the pole; upper: the pole, the harp and the
    shade (lit when on)."""
    if part == "lower":
        els = octagon("Base", 8, 8, 3.5, 0, 0.75, "p-darksteel")
        els += octagon("Dome", 8, 8, 2.25, 0.75, 1.75, "p-brass")
        els += [B("Pole", (7.5, 1.75, 7.5), (8.5, 16, 8.5), "p-brass", faces=no("up", "down")),
                B("Collar", (7.25, 9, 7.25), (8.75, 9.75, 8.75), "p-brass"),
                B("Cable", (8.5, 0, 8), (12, 0.4, 8.5), "p-black"),
                B("Switch", (11.5, 0, 7.5), (13, 0.75, 9), "p-black")]
        return els
    shade = "p-shadelit" if on else "p-shade"
    g = 190 if on else 0
    els = [B("Pole", (7.5, 0, 7.5), (8.5, 6, 8.5), "p-brass", faces=no("down")),
           B("Socket", (7.1, 6, 7.1), (8.9, 7.5, 8.9), "p-brass"),
           B("Bulb", (7.2, 7.5, 7.2), (8.8, 9.5, 8.8), "p-bulb" if on else "p-white", glow=255 if on else 0),
           B("HarpW", (4.5, 7, 7.75), (5, 11.5, 8.25), "p-brass"), B("HarpE", (11, 7, 7.75), (11.5, 11.5, 8.25), "p-brass"),
           B("HarpBar", (5, 7, 7.75), (11, 7.5, 8.25), "p-brass"),
           B("Finial", (7.4, 11.25, 7.4), (8.6, 12.5, 8.6), "p-brass"),
           B("Chain", (9.8, 3, 7.9), (10.1, 6.5, 8.2), "p-brass"), B("ChainEnd", (9.6, 2.5, 7.7), (10.3, 3, 8.4), "p-brass")]
    # round 4: a tapered shade (three tiers narrowing upward), a brass trim at its hem and its top
    for k, (r, y1, y2) in enumerate(((5.2, 4.5, 6.7), (4.6, 6.7, 8.9), (4.0, 8.9, 11))):
        els += octagon(f"Shade{k}", 8, 8, r, y1, y2, shade, step=0.01)
    els += octagon("TrimLow", 8, 8, 5.4, 4.25, 5, "p-brass", faces=("north", "south", "east", "west", "down"))
    els += octagon("TrimTop", 8, 8, 4.2, 10.5, 11.25, "p-brass", faces=("north", "south", "east", "west", "up"))
    if on:
        glow([e for e in els if e["name"].startswith("Shade")], g)
    return els


def magtable():
    """A low waiting-room table, laminate on chrome legs, with magazines and brochures of unusual contents."""
    els = MK.table("Table", 1.5, 2.5, 14.5, 13.5, 6.5, 1.0, 0.75, 1.0, 1.25, 0.75, top={"top": "p-worktop", "side": "p-teal"},
                   legs="p-chrome")
    els.append(B("Shelf", (2.5, 2, 3.5), (13.5, 2.5, 12.5), "p-darksteel"))
    els += turned([pic(B("MagA", (2.5, 6.5, 3.5), (8, 6.7, 10.5), "p-papers", faces=no("down")), "up", "p-magazine")], ry=12, origin=(5.2, 6.5, 7))
    els += turned([pic(B("MagB", (6.5, 6.7, 5), (12.5, 6.9, 12), "p-papers", faces=no("down")), "up", "p-magazine")], ry=-22, origin=(9.5, 6.7, 8.5))
    els += turned([pic(B("Bro", (9.5, 6.5, 3.5), (13, 6.7, 7.5), "p-papers", faces=no("down")), "up", "p-brochure")], ry=30, origin=(11.2, 6.5, 5.5))
    els += turned([pic(B("BroFold", (3.5, 6.5, 10), (7, 8.5, 10.3), "p-papers"), "north", "p-brochure")], rx=-55, origin=(5.2, 6.5, 10.15))
    for i, y in enumerate((2.5, 2.75, 3.0)):
        els += turned([pic(B(f"Stack{i}", (4 + i * 0.5, y, 4.5), (10 + i * 0.5, y + 0.25, 11.5), "p-papers", faces=no("down")),
                           "up", "p-magazine" if i == 2 else "p-papers")], ry=(-6 + i * 7), origin=(7.5, y, 8))
    els += soda_bottle("Soda", 12.25, 11.25, 6.5, "p-bottlebrown", "p-sodalabel2", r=0.9, h=4)
    return els


def sodas():
    """Musty soft-drink bottles on the floor, one with a stale brown inch in it, one fallen and rolled."""
    els = soda_bottle("A", 4, 4, 0, "p-bottlestale")
    els += soda_bottle("B", 6.6, 6, 0, "p-bottlegreen", "p-sodalabel2", r=1.0, h=5)
    els += soda_bottle("C", 11.5, 4.5, 0, "p-bottlebrown")
    els += turned(soda_lying("D", 4, 10, 1.15, 11.5, "p-bottlegreen"), ry=25, origin=(7, 1.15, 11.5))
    els += turned([B("Spill", (8, 0, 9), (14, 0.06, 13), "p-mould", faces=("up",))], ry=10, origin=(11, 0, 11))
    els += turned([pic(B("Leaflet", (10, 0, 7.5), (13.5, 0.15, 11.5), "p-papers", faces=no("down")), "up", "p-brochure")], ry=-30, origin=(11.75, 0, 9.5))
    return els


# ======================================================================== Beds

def bed_frame(rails_down=()):
    """A white hospital bed 32 long, the foot at z 0 (north) and the head at z 32 (south): castors, a base frame and a
    lift shroud, a deck, a headboard and a footboard, split side rails (head and foot, both sides)."""
    W = "p-whiteworn"
    els = []
    for i, (x, z) in enumerate(((2.75, 3), (13.25, 3), (2.75, 29), (13.25, 29))):
        els += castor(f"Castor{i}", x, z)
    els += [B("BaseW", (2, 2.25, 2), (3.5, 3.5, 30), W), B("BaseE", (12.5, 2.25, 2), (14, 3.5, 30), W),
            B("BaseN", (3.5, 2.25, 2.25), (12.5, 3.25, 3.75), W, faces=no("east", "west")),
            B("BaseS", (3.5, 2.25, 28.25), (12.5, 3.25, 29.75), W, faces=no("east", "west")),
            B("Shroud", (4, 2.5, 9), (12, 4.5, 23), W),
            B("LiftN", (6.5, 4.5, 6), (9.5, 7, 9), "p-darksteel", faces=no("up", "down")),
            B("LiftS", (6.5, 4.5, 23), (9.5, 7, 26), "p-darksteel", faces=no("up", "down")),
            B("Deck", (1.25, 7, 1.25), (14.75, 8.25, 30.75), W),
            B("Pedal", (6, 2.75, 30), (10, 3.25, 31.5), "p-darksteel")]
    # headboard (south) and footboard (north): tube posts, a moulded panel, a top rail
    els += [B("HeadPostW", (0.75, 3, 30.5), (2.25, 19.5, 32), "p-white"), B("HeadPostE", (13.75, 3, 30.5), (15.25, 19.5, 32), "p-white"),
            B("HeadPanel", (2.25, 7.5, 30.75), (13.75, 18.5, 31.75), {"all": "p-white", "north": "p-whiteworn"}),
            B("HeadInset", (3.25, 9, 30.5), (12.75, 17, 30.75), "p-whiteworn", faces=("north", "up", "down", "east", "west")),
            B("HeadTop", (0.5, 18.75, 30.25), (15.5, 19.75, 32), "p-white"),
            B("FootPostW", (0.75, 3, 0), (2.25, 16, 1.5), "p-white"), B("FootPostE", (13.75, 3, 0), (15.25, 16, 1.5), "p-white"),
            B("FootPanel", (2.25, 7.5, 0.25), (13.75, 15, 1.25), {"all": "p-white", "south": "p-whiteworn"}),
            B("FootTop", (0.5, 15, 0), (15.5, 16, 1.75), "p-white"),
            B("ChartBoard", (5, 8.5, -0.3), (11, 14, 0.25), "p-greyplastic", faces=no("south")),
            pic(B("Chart", (5.5, 9, -0.4), (10.5, 13.25, -0.3), "p-papers", faces=("north",)), "north", "p-chart"),
            B("ChartClip", (7, 13.25, -0.6), (9, 14.25, -0.25), "p-chrome")]
    # split side rails: head rails z 17.5-29, foot rails z 3-14.5; "down" ones folded low
    for side, x in (("W", 0.4), ("E", 14.85)):
        for part, z1, z2 in (("H", 17.5, 29), ("F", 3, 14.5)):
            low = (side + part) in rails_down
            ytop = 10.25 if low else 15
            els += [B(f"Rail{side}{part}Top", (x, ytop - 1, z1), (x + 0.75, ytop, z2), "p-white"),
                    B(f"Rail{side}{part}Mid", (x + 0.1, ytop - 3.25, z1 + 0.75), (x + 0.65, ytop - 2.75, z2 - 0.75), "p-chrome"),
                    B(f"Rail{side}{part}PostA", (x + 0.05, 8.25 if not low else 7, z1 + 0.75), (x + 0.7, ytop - 1, z1 + 1.5), "p-chrome", faces=no("up", "down")),
                    B(f"Rail{side}{part}PostB", (x + 0.05, 8.25 if not low else 7, z2 - 1.5), (x + 0.7, ytop - 1, z2 - 0.75), "p-chrome", faces=no("up", "down"))]
    els += [B("MossA", (12.5, 3.5, 28.5), (14.5, 4.25, 30.5), "p-moss"), B("MossB", (2, 3.5, 1.5), (3.25, 4, 3), "p-moss")]
    return els


def bed_model(kind):
    """The whole bed (32 long) for kind made, stripped or strap."""
    els = bed_frame(rails_down=("EF",) if kind == "made" else ())
    if kind == "stripped":
        els.append(B("Mattress", (1.5, 8.25, 1.5), (14.5, 11.5, 30.5), {"top": "p-mattress", "side": "p-mattress-side"}))
        els += turned([B("HeapA", (2.5, 11.5, 2.5), (11, 13, 8), "p-sheetstain")], ry=12, origin=(6.5, 11.5, 5))
        els += turned([B("HeapB", (5, 12.5, 3.5), (12.5, 14, 7.5), "p-sheetstain")], ry=-20, origin=(8.5, 12.5, 5.5))
        els += turned([B("HeapC", (9, 9.5, 5), (14.6, 13, 6.5), "p-sheetstain")], rz=-14, origin=(14.5, 13, 5.75))
        els += turned([B("Pillow", (3.5, 11.5, 24), (12.5, 13.25, 29.5), "p-pillow")], ry=-18, origin=(8, 11.5, 26.75))
    else:
        sheet = "p-sheetstain" if kind == "strap" else "p-sheet"
        els.append(B("Mattress", (1.5, 8.25, 1.5), (14.5, 11.5, 30.5), {"top": sheet, "side": sheet}))
        els += turned([B("Pillow", (3, 11.5, 25), (13, 13.5, 30), "p-pillow")], rx=-6, origin=(8, 11.5, 30))
        if kind == "made":
            els += [B("Blanket", (1.25, 11.5, 2), (14.75, 12.25, 19.75), {"top": "p-blanket", "side": "p-blanket-side"}),
                    B("BlanketW", (0.95, 9, 2), (1.5, 12.25, 19.75), "p-blanket-side", faces=no("up", "down")),
                    B("BlanketE", (14.5, 9, 2), (15.05, 12.25, 19.75), "p-blanket-side", faces=no("up", "down")),
                    B("Turn", (1.1, 11.5, 19.5), (14.9, 12.75, 22), "p-sheet")]
        else:
            # restraint straps over the chest, hips and ankles, buckled; wrist cuffs hanging off the head rails
            for i, z in enumerate((22, 13.5, 3.5)):
                els += [B(f"Strap{i}", (1.3, 11.5, z), (14.7, 11.9, z + 1.75), "p-leather", faces=no("down")),
                        B(f"StrapW{i}", (1.0, 7.25, z), (1.5, 11.9, z + 1.75), "p-leather", faces=no("up")),
                        B(f"StrapE{i}", (14.5, 7.25, z), (15.0, 11.9, z + 1.75), "p-leather", faces=no("up")),
                        B(f"Buckle{i}", (9, 11.9, z - 0.15), (10.5, 12.2, z + 1.9), "p-chrome", faces=no("down"))]
            for s, x in (("W", 0.1), ("E", 15.15)):
                els += [B(f"Cuff{s}", (x, 10, 19.25), (x + 0.75, 13.75, 21.25), "p-leather"),
                        B(f"CuffRing{s}", (x - 0.1, 12.5, 19.9), (x + 0.85, 13.1, 20.6), "p-chrome")]
            els.append(pic(B("Stain", (5, 11.52, 14.5), (11, 11.56, 19.5), "p-blood", faces=("up",)), "up", "p-bloodpool"))
    return els


def bed(part, kind):
    els = bed_model(kind)
    return clip_z(els, 16, 99, -16) if part == "head" else clip_z(els, -99, 16, 0)


# ======================================================================== Curtain, overbed table, monitor, ventilator, crib, teddy

def curtain(part):
    """A pale green privacy curtain, drawn, along the block's north edge. upper: the ceiling track (on drop rods up
    to the ceiling a block above), gliders, the open mesh band and the top of the curtain; lower: the curtain to a
    hem just off the floor. The cloth is pleated: alternate strips stand forward and back."""
    els = []
    if part == "upper":
        els += [B("Track", (0, 15, 0.5), (16, 15.75, 1.75), "p-chrome"),
                B("RodA", (3.6, 15.75, 0.85), (4.4, 32, 1.4), "p-chrome", faces=no("down")),
                B("RodB", (11.6, 15.75, 0.85), (12.4, 32, 1.4), "p-chrome", faces=no("down"))]
        for i in range(8):
            x = 1 + i * 2
            els.append(B(f"Glider{i}", (x - 0.3, 14, 0.85), (x + 0.3, 15, 1.4), "p-chrome", faces=no("up")))
    for i in range(8):
        x1, x2 = i * 2, i * 2 + 2
        z1, z2 = (0.55, 1.05) if i % 2 == 0 else (1.0, 1.5)
        if part == "upper":
            els.append(B(f"Mesh{i}", (x1, 10, z1 + 0.1), (x2, 14, z2 - 0.1), "p-curtainmesh", faces=("north", "south")))
            els.append(B(f"Cloth{i}", (x1, 0, z1), (x2, 10, z2), "p-curtain", faces=("north", "south", "east", "west", "up")))
        else:
            els.append(B(f"Cloth{i}", (x1, 2.25, z1), (x2, 16, z2), "p-curtain", faces=("north", "south", "east", "west")))
            els.append(B(f"Hem{i}", (x1, 1.0, z1 - 0.05), (x2, 2.25, z2 + 0.05), "p-curtainhem", faces=("north", "south", "east", "west", "down")))
    return els


def overbed():
    """An over-bed table: a base on castors along one side, a column, a laminate top cantilevered across, a paper cup
    and a jug left on it as if the patient had only just gone."""
    W = "p-whiteworn"
    els = [B("BaseZ", (1.25, 2.25, 1), (3.25, 3.25, 15), W), B("BaseX", (3.25, 2.25, 7), (13.5, 3.0, 8.75), W)]
    for i, (x, z) in enumerate(((2.25, 1.9), (2.25, 14.1), (12.75, 7.9))):
        els += castor(f"Castor{i}", x, z)
    els += [B("Column", (1.5, 3.25, 6.75), (3.5, 10, 9.25), W),
            B("Inner", (1.9, 10, 7.15), (3.1, 12.5, 8.85), "p-chrome"),
            B("Arm", (1.5, 12.5, 7), (9, 13.25, 9), "p-steel"),
            B("Top", (1, 13.25, 3), (15, 14.25, 13), {"top": "p-worktop", "side": "p-teal"})]
    els += MK.rim("Rim", (1, 13.25, 3), (15, 14.25, 13), "p-teal", w=0.5, h=0.5)
    els += octagon("Cup", 5, 7, 0.85, 14.25, 16.75, {"side": "p-white", "top": "p-liqamber"})
    els += octagon("Jug", 10, 8.5, 1.6, 14.25, 18.5, {"side": "p-greyplastic", "top": "p-greyplastic"})
    els += [B("JugHandle", (11.6, 15, 8), (12.4, 18, 9), "p-greyplastic"),
            B("JugLid", (8.6, 18.5, 7.1), (11.4, 19, 9.9), "p-blanket-side")]
    els += turned([pic(B("Card", (3, 14.25, 9), (7, 14.4, 12), "p-papers", faces=no("down")), "up", "p-chart")], ry=-10, origin=(5, 14.25, 10.5))
    return els


def five_star(name, y=0.6, arm=5.5, tex="p-darksteel"):
    """A five-armed wheeled base about the block centre (as an IV stand's), a castor at each arm's end."""
    els = [B(name + "Hub", (7, y - 0.1, 7), (9, y + 1.5, 9), tex)]
    for k in range(5):
        a = k * 72
        els.append(B(f"{name}Arm{k}", (7.6, y, 8 - arm), (8.4, y + 0.8, 8), tex, rot=(0, a, 0), origin=(8, y, 8)))
        x, z = 8 - (arm - 0.4) * math.sin(math.radians(a)), 8 - (arm - 0.4) * math.cos(math.radians(a))
        els += [B(f"{name}Wheel{k}", (x - 0.35, 0, z - 0.5), (x + 0.35, y + 0.1, z + 0.5), "p-black")]
    return els


def monitor(on):
    """A vital-signs monitor on a wheeled pole, its screen to the north: on, a green trace and numbers (it glows)."""
    els = five_star("Base")
    els += [B("Pole", (7.5, 2, 7.5), (8.5, 9, 8.5), "p-chrome", faces=no("down")),
            B("Mount", (6.5, 8.5, 7.25), (9.5, 9.5, 9.5), "p-darksteel"),
            B("Basket", (5, 5, 8.75), (11, 7, 11), "p-chrome", faces=no("up")),
            B("BasketIn", (5.25, 6.5, 9), (10.75, 6.75, 10.75), "p-darksteel", faces=("up",)),
            B("Body", (2.5, 9, 6), (13.5, 15.5, 11), {"all": "p-greyplastic", "front": "p-greyplastic"}),
            B("Bezel", (2.75, 9.25, 5.75), (13.25, 15.25, 6), "p-darkplastic", faces=no("south")),
            pic(B("Screen", (3.25, 9.75, 5.6), (11, 14.75, 5.75), "p-black", faces=("north",)), "north",
                "p-monitoron" if on else "p-monitoroff", glow=170 if on else 0),
            B("Handle", (5, 15.5, 8), (11, 16.25, 9), "p-darkplastic"),
            B("Cable", (12, 3, 9.5), (12.5, 9, 10), "p-black")]
    for i, y in enumerate((10.25, 11.75, 13.25)):
        els.append(B(f"Button{i}", (11.4, y, 5.4), (12.75, y + 1, 5.75), "p-greyplastic" if i else ("p-liqred" if on else "p-darkplastic"),
                     faces=no("south"), glow=200 if (on and i == 0) else 0))
    return els


def ventilator():
    """An ICU ventilator on a wheeled stand: a white unit with its control face to the north, blue corrugated hoses
    looping out of it, a humidifier chamber at the side, a handle across the top."""
    W = "p-whiteworn"
    els = [B("Base", (2.5, 1.25, 3), (13.5, 2.25, 13), "p-darksteel")]
    for i, (x, z) in enumerate(((3.5, 4), (12.5, 4), (3.5, 12), (12.5, 12))):
        els += [B(f"Wheel{i}", (x - 0.4, 0, z - 0.6), (x + 0.4, 1.25, z + 0.6), "p-black")]
    els += [B("Column", (6.5, 2.25, 7), (9.5, 6.5, 10), "p-chrome"),
            B("Unit", (2, 6.5, 4.5), (14, 15, 13), {"all": W, "front": "p-white"}),
            pic(B("Face", (2.75, 7.25, 4.25), (13.25, 14.25, 4.5), "p-white", faces=no("south")), "north", "p-ventface"),
            B("Handle", (3, 15.5, 11.5), (13, 16.25, 12.25), "p-darkplastic"),
            B("HandleW", (3, 15, 11.5), (3.75, 15.5, 12.25), "p-darkplastic"), B("HandleE", (12.25, 15, 11.5), (13, 15.5, 12.25), "p-darkplastic"),
            B("PortA", (10.5, 6.75, 3.5), (11.75, 8, 4.5), "p-greyplastic"), B("PortB", (12.25, 6.75, 3.5), (13.5, 8, 4.5), "p-greyplastic"),
            # the hoses: down from the ports, looping round in front and back up to the humidifier at the side
            B("HoseA", (10.6, 2.75, 2.5), (11.6, 7, 3.5), "p-hose"), B("HoseB", (12.3, 3.5, 2.75), (13.3, 7, 3.75), "p-hose"),
            B("HoseLoop", (1, 2.75, 2.5), (11.6, 3.75, 3.5), "p-hose"),
            B("HoseUp", (1, 3.75, 2.5), (2, 9.5, 3.5), "p-hose"),
            B("HoseToHum", (1, 9.5, 2.5), (2, 10.5, 6.5), "p-hose"),
            B("Hum", (0.4, 8, 6.5), (2, 12, 9.5), {"all": "p-tube", "top": "p-greyplastic"}),
            B("HumWater", (0.3, 8.25, 6.75), (0.4, 9.5, 9.25), "p-liqblue", faces=("west",)),
            B("HoseLoose", (12.3, 3, 1), (13.3, 4, 3.75), "p-hose"),
            B("Mask", (11.5, 0, 0), (14.5, 1, 2.5), "p-acrylic")]
    return els


def crib():
    """A maternity bassinet: a clear acrylic tub on a white trolley, a crumpled pink blanket inside, the name card on
    its end, a folded blanket on the shelf below."""
    W = "p-whiteworn"
    els = []
    for i, (x, z) in enumerate(((2.75, 3.25), (13.25, 3.25), (2.75, 12.75), (13.25, 12.75))):
        els += castor(f"Castor{i}", x, z)
        els.append(B(f"Leg{i}", (x - 0.5, 2.25, z - 0.5), (x + 0.5, 8, z + 0.5), "p-chrome", faces=no("up", "down")))
    els += [B("Shelf", (2.4, 3.5, 2.9), (13.6, 4, 13.1), W),
            B("Folded", (4, 4, 5), (11, 5.25, 11), {"top": "p-babyblanketblue", "side": "p-linenstack"}),
            B("Frame", (1.5, 8, 2), (14.5, 9, 14), W),
            B("Floor", (2.25, 9, 2.75), (13.75, 9.5, 13.25), "p-white"),
            B("Pad", (2.75, 9.5, 3.25), (13.25, 10.5, 12.75), {"top": "p-sheet", "side": "p-sheet"})]
    els += turned([B("Blanket", (3.5, 10.5, 4.5), (11.5, 11.4, 10.5), "p-babyblanket")], ry=12, origin=(7.5, 10.5, 7.5))
    els += turned([B("BlanketFold", (7, 10.5, 8), (12.5, 12.25, 9.5), "p-babyblanket")], ry=-25, rx=0, origin=(9.5, 10.5, 9))
    els += [transparent(B("WallN", (2, 9, 2.25), (14, 14.5, 2.75), "p-acrylic", faces=("north", "south", "up"))),
            transparent(B("WallS", (2, 9, 13.25), (14, 14.5, 13.75), "p-acrylic", faces=("north", "south", "up"))),
            transparent(B("WallW", (2, 9, 2.75), (2.5, 14.5, 13.25), "p-acrylic", faces=("east", "west", "up"))),
            transparent(B("WallE", (13.5, 9, 2.75), (14, 14.5, 13.25), "p-acrylic", faces=("east", "west", "up"))),
            pic(B("Card", (5, 11.5, 1.9), (11, 14, 2.05), "p-white", faces=("north",)), "north", "p-cribcard")]
    return els


def teddy():
    """A worn stuffed teddy bear sitting, facing north: one button eye gone, a red patch on its tummy."""
    T, MZ = "p-teddy", "p-teddymuzzle"
    els = [B("Body", (5.5, 0.5, 7.25), (10.5, 5.75, 11), T),
           B("Tummy", (6.5, 1.25, 7), (9.5, 4.75, 7.25), MZ, faces=no("south")),
           B("Patch", (8.75, 3.25, 6.9), (10, 4.5, 7.05), "p-teddypatch", faces=("north",)),
           B("LegL", (5.25, 0, 3.25), (7.5, 2.25, 8), T), B("LegR", (8.5, 0, 3.25), (10.75, 2.25, 8), T),
           B("PadL", (5.5, 0.25, 3.05), (7.25, 2, 3.25), MZ, faces=("north",)), B("PadR", (8.75, 0.25, 3.05), (10.5, 2, 3.25), MZ, faces=("north",))]
    els += turned([B("ArmL", (3.75, 2, 7.75), (5.5, 5.5, 9.75), T)], rz=18, origin=(5.5, 5.5, 8.75))
    els += turned([B("ArmR", (10.5, 2, 7.75), (12.25, 5.5, 9.75), T)], rz=-12, origin=(10.5, 5.5, 8.75))
    head = [B("Head", (5.25, 5.5, 6.75), (10.75, 10, 11), T),
            B("Muzzle", (6.75, 5.9, 6), (9.25, 7.75, 6.75), MZ),
            B("Nose", (7.4, 7.1, 5.75), (8.6, 7.75, 6), "p-black", faces=no("south")),
            B("Eye", (6.25, 8.1, 6.5), (7.1, 8.9, 6.75), "p-black", faces=no("south")),
            B("Thread", (8.9, 8.3, 6.6), (9.7, 8.6, 6.75), MZ, faces=("north",)),
            B("EarL", (4.75, 9.5, 8), (6.5, 11.25, 9.25), T), B("EarR", (9.5, 9.5, 8), (11.25, 11.25, 9.25), T),
            B("EarInL", (5.1, 9.85, 7.85), (6.15, 10.9, 8), MZ, faces=("north",)), B("EarInR", (9.85, 9.85, 7.85), (10.9, 10.9, 8), MZ, faces=("north",))]
    els += turned(head, rz=7, origin=(8, 5.5, 9))
    return els


# ======================================================================== Ward desk, medical cabinet

def desk2():
    """A white ward desk, its kneehole to the north, a drawer pedestal at its east end, a vinyl chair tucked in and the
    day's charts left on it."""
    W = "p-white"
    els = [B("Top", (0.5, 11.5, 3), (15.5, 12.5, 15), {"top": "p-white", "side": "p-whiteworn"}),
           B("GableW", (0.75, 0, 3.5), (1.75, 11.5, 14.75), "p-whiteworn"),
           B("Modesty", (1.75, 3, 13.75), (10, 11.5, 14.5), "p-whiteworn", faces=no("up", "down")),
           B("Pedestal", (10, 0, 3.5), (15.25, 11.5, 14.75), "p-whiteworn"),
           B("Kick", (10.25, 0, 3.25), (15, 1, 3.5), "p-darksteel", faces=("north",))]
    for i, (y1, y2) in enumerate(((1.25, 5.5), (5.75, 8.5), (8.75, 11.25))):
        els += [B(f"Drawer{i}", (10.25, y1, 3.1), (15, y2, 3.5), W, faces=no("south")),
                B(f"Pull{i}", (11.75, y2 - 1.25, 2.6), (13.5, y2 - 0.75, 3.1), "p-chrome", faces=no("south"))]
    chair = MK.chair("Chair", 10, 12, 8, 8, 7.5, 7.5, 0.75, 1.25, seat={"top": "p-vinyl", "side": "p-vinyl-side"},
                     frame="p-chrome", back={"front": "p-vinyl", "back": "p-vinyl-side", "side": "p-chrome", "top": "p-chrome"})
    els += turn(chair, 2)
    els += [B("Clipboard", (2.5, 12.5, 6), (6.5, 12.75, 11), "p-veneer-side", faces=no("down")),
            pic(B("ClipSheet", (2.75, 12.75, 6.5), (6.25, 12.85, 10.75), "p-papers", faces=no("down")), "up", "p-chart"),
            B("ClipJaw", (3.75, 12.75, 10.2), (5.25, 13.1, 10.7), "p-chrome")]
    els += turned([B("Folder", (7, 12.5, 5), (11.5, 13, 10.5), {"top": "p-folder", "side": "p-papers"})], ry=-10, origin=(9.25, 12.5, 7.75))
    els += octagon("Pens", 13, 11.5, 0.9, 12.5, 14.5, {"side": "p-greyplastic", "top": "p-black"})
    els += [B("PenA", (12.7, 14.5, 11.2), (13, 16, 11.5), "p-liqblue"), B("PenB", (13.1, 14.5, 11.6), (13.4, 15.7, 11.9), "p-black")]
    els += octagon("Mug", 13.25, 6, 0.9, 12.5, 14.25, {"side": "p-white", "top": "p-black"})
    return els


def cab_items(prefix, y, z1=6.5, seed=0):
    """Bottles, pill tubs and boxes standing on a cabinet shelf at height y."""
    lay = [("brown", 3.2), ("pill", 5.2), ("box", 7.5), ("brown", 10.2), ("pill", 11.8), ("tall", 13.2)]
    if seed % 2:
        lay = [("box", 3.5), ("tall", 6.2), ("pill", 7.8), ("brown", 9.6), ("box", 12)]
    els = []
    for i, (k, x) in enumerate(lay):
        n = f"{prefix}{i}"
        z = z1 + (i % 2) * 2
        if k == "brown":
            els += [B(n, (x - 0.8, y, z - 0.8), (x + 0.8, y + 2.75, z + 0.8), "p-bottlebrown"),
                    B(n + "Neck", (x - 0.4, y + 2.75, z - 0.4), (x + 0.4, y + 3.5, z + 0.4), "p-white")]
        elif k == "tall":
            els += [B(n, (x - 0.7, y, z - 0.7), (x + 0.7, y + 3.75, z + 0.7), "p-tube"),
                    B(n + "Cap", (x - 0.45, y + 3.75, z - 0.45), (x + 0.45, y + 4.25, z + 0.45), "p-cap")]
        elif k == "pill":
            els += [B(n, (x - 0.75, y, z - 0.75), (x + 0.75, y + 2, z + 0.75), {"side": "p-pillbottle", "top": "p-white"}),
                    B(n + "Cap", (x - 0.85, y + 2, z - 0.85), (x + 0.85, y + 2.5, z + 0.85), "p-white")]
        else:
            els.append(pic(B(n, (x - 1.25, y, z - 1), (x + 1.25, y + 2.5, z + 1), "p-white"), "north", "p-pillbox"))
    return els


def glass_cabinet(part, body, glass_tex=("p-glass", "p-glass"), back="p-cabback", items=cab_items, base=6.0, knives=False):
    """A tall cabinet two blocks high with glazed doors (lower: a plinth and two drawers under the glass; upper: the
    glass to a cornice). body is the carcass material."""
    els = []
    lower = part == "lower"
    if lower:
        y0, y1 = 0, 16
        els += [B("Plinth", (1.5, 0, 3.5), (14.5, 1.5, 14.5), "p-black", faces=("north", "east", "west")),
                B("Floor", (1, 1.5, 3), (15, 2.5, 15), body, faces=no("down"))]
        dy = 2.5
        for i, (a, b) in enumerate(((dy, dy + (base - dy) / 2 - 0.1), (dy + (base - dy) / 2 + 0.1, base))):
            els += [B(f"Drawer{i}", (1.25, a, 2.5), (14.75, b, 3.05), body, faces=no("south")),
                    B(f"Pull{i}", (6.5, (a + b) / 2 - 0.3, 2), (9.5, (a + b) / 2 + 0.3, 2.5), "p-chrome", faces=no("south"))]
        els.append(B("Rail", (1, base, 2.5), (15, base + 0.75, 3.05), body, faces=no("south")))
        gy1, gy2 = base + 0.75, 16
        shelves = [base + 0.75, 11.5]
    else:
        y0, y1 = 0, 14
        els += [B("Cornice", (0.5, 14, 2.25), (15.5, 16, 15.5), body),
                B("RailTop", (1, 13.25, 2.5), (15, 14, 3.05), body, faces=no("south"))]
        gy1, gy2 = 0, 13.25
        shelves = [3.5, 8.5]
    els += [B("SideW", (1, 1.5 if lower else y0, 3), (1.75, y1, 15), body, faces=no("up", "down")),
            B("SideE", (14.25, 1.5 if lower else y0, 3), (15, y1, 15), body, faces=no("up", "down")),
            B("Back", (1.75, 2.5 if lower else y0, 14.25), (14.25, y1, 15), {"all": body, "front": back}, faces=("north", "south"))]
    for i, y in enumerate(shelves):
        if i or not lower:
            els.append(B(f"Shelf{i}", (1.75, y - 0.4, 3.5), (14.25, y, 14.25), body, faces=("up", "down", "north")))
        if knives:
            els += knife_row(f"Knives{i}", y)
        else:
            els += items(f"Item{i}", y, seed=i + (0 if lower else 2))
    # the glazed doors: stiles, the glass in two leaves, handles at the meeting stiles
    els += [B("StileW", (1, gy1, 2.5), (2, gy2, 3.05), body, faces=no("south")),
            B("StileE", (14, gy1, 2.5), (15, gy2, 3.05), body, faces=no("south")),
            B("StileMid", (7.6, gy1, 2.45), (8.4, gy2, 3.05), body, faces=no("south"))]
    for i, (x1, x2) in enumerate(((2, 7.6), (8.4, 14))):
        els.append(transparent(B(f"Glass{i}", (x1, gy1, 2.7), (x2, gy2, 2.85), glass_tex[i], faces=("north", "south"))))
    if lower:
        els += [B("HandleA", (6.9, 8.5, 2), (7.3, 11.5, 2.45), "p-chrome"), B("HandleB", (8.7, 8.5, 2), (9.1, 11.5, 2.45), "p-chrome"),
                B("Lock", (7.65, 10, 2.3), (8.35, 10.7, 2.45), "p-brass")]
    return els


def knife_row(prefix, y):
    """A magnetic bar across the back of a shelf and blades hanging from it in front of the painted rows."""
    els = [B(prefix + "Bar", (2, y + 3.25, 13.25), (14, y + 4, 14.25), "p-darksteel")]
    for i, x in enumerate((2.75, 4.25, 5.5, 7, 9, 10.5, 12, 13.25)):
        long = i % 3 != 1
        els += [B(f"{prefix}H{i}", (x - 0.3, y + 3.5, 12.9), (x + 0.3, y + 4.6, 13.25), "p-black"),
                B(f"{prefix}B{i}", (x - 0.35 if long else x - 0.2, y + (0.75 if long else 2), 12.95), (x + 0.35 if long else x + 0.2, y + 3.5, 13.15), "p-blade")]
    return els


def cabinet(part):
    els = glass_cabinet(part, "p-white")
    if part == "upper":
        els += [B("CrossV", (7.25, 14.25, 2.05), (8.75, 15.75, 2.25), "p-cap", faces=no("south")),
                B("CrossH", (6.5, 14.6, 2.0), (9.5, 15.4, 2.25), "p-cap", faces=no("south"))]
    return els
