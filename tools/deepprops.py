"""Models for the deep-level props of the graphics pass's "deep props" round (textures: deepprops_tex.py).

    sign()               Level 6.1's neon food-court sign, a case on the wall (the decoration's own wall is the wood panelling)
    exit_door(upper)     the exit door's lower and upper block, as geometry (four-sided: the block has no facing)
    kitchen_door(upper)  the kitchen's swing doors, the same
    tool_shelf()         Level 9's steel shelving with tools hung on a pegboard
    tool_rack()          Level 10's wooden rack with a shovel, fork, hoe and rake hung on it
    nail_barrel()        a coopered barrel with iron hoops and a heap of nails at the top
    feed_trough()        a plank trough on trestle legs, feed at one end and rainwater at the other
    hand_pump()          a cast-iron pitcher pump on a concrete plinth

Doors have no facing, so the leaf, frame and hardware are built for the north face and turned four times about the
block centre (`MK.turn`); every part of them stays inside the block and the hardware stops short of its planes
(graphics pass B8's lesson), so nothing sits on the neighbouring wall's face.
"""
import math

import modelkit as MK
from gen_shapes import octo_plates, octagon

B = MK.box
PX = MK.PX
ALL4 = ("north", "east", "south", "west")


def turned(els):
    """The north-facing parts `els` on all four sides of the block."""
    out = []
    for k in range(4):
        out += MK.turn(els, k) if k else els
    return out


# ---------------- Level 6.1: the signs ----------------

def sign(key):
    """A neon sign 15 units wide and 10 high on the wall's face (z 0 is the wall): a dark metal case 1 deep with a
    half-unit rim, the lit face set back in it, and a pair of standoff lugs at the top. The case is the sign's own
    box; the wall behind it is the panelling."""
    x1, x2, y1, y2, z1 = 0.5, 15.5, 3.0, 13.0, -1.0
    rim = 0.5
    els = [B("RimT", (x1, y2 - rim, z1), (x2, y2, 0), "dp-signcase", faces=("north", "up", "east", "west")),
           B("RimB", (x1, y1, z1), (x2, y1 + rim, 0), "dp-signcase", faces=("north", "down", "east", "west")),
           B("RimL", (x1, y1 + rim, z1), (x1 + rim, y2 - rim, 0), "dp-signcase", faces=("north", "west")),
           B("RimR", (x2 - rim, y1 + rim, z1), (x2, y2 - rim, 0), "dp-signcase", faces=("north", "east")),
           B("Face", (x1 + rim, y1 + rim, -0.6), (x2 - rim, y2 - rim, -0.5), key, faces=("north",), glow=230, uv=[0, 0, 14, 9]),
           B("LugL", (2.5, y2, -0.8), (3.5, y2 + 0.5, -0.2), "dp-iron", faces=("north", "up", "east", "west")),
           B("LugR", (12.5, y2, -0.8), (13.5, y2 + 0.5, -0.2), "dp-iron", faces=("north", "up", "east", "west"))]
    return els


# ---------------- Door frames ----------------

POST = 1.5      # corner post and head rail
RECESS = 1.5    # how far the leaf stands back from the block's face


def door_frame(upper, tex):
    """The jamb: four corner posts the block's whole height (so it reads the same from any side), and in the upper
    block a head rail on each face. The leaf is a core filling the middle, its face RECESS back from the block's."""
    els = []
    for i, (x, z) in enumerate(((0, 0), (16 - POST, 0), (0, 16 - POST), (16 - POST, 16 - POST))):
        els.append(B(f"Post{i}", (x, 0, z), (x + POST, 16, z + POST), tex, faces=ALL4 + (("up",) if upper else ())))
    if upper:
        head = [B("Head", (POST, 16 - POST, 0), (16 - POST, 16, POST), tex, faces=("north", "up", "down"))]
        els += turned(head)
    return els


def door_core(upper, leaf):
    """The leaf as one core box with the leaf texture on its four sides."""
    return [B("Core", (POST, 0, POST), (16 - POST, 16, 16 - POST), {"all": leaf}, faces=ALL4 + (("up",) if upper else ()))]


# ---------------- Exit door ----------------

def exit_door(upper):
    leaf = "dp-exitleaf-" + ("upper" if upper else "lower")
    els = door_frame(upper, "dp-exitframe") + door_core(upper, leaf)
    z0 = RECESS - 0.05  # the plane the hardware stands from (just in front of the leaf's face)
    hw = []
    if not upper:
        # a kick plate at the foot, a push bar across at hand height, three hinge leaves down the left edge
        hw += MK.kick_plate("Kick", 2.5, 13.5, 0.5, 4.5, RECESS, tex="dp-exitkick", t=0.3)
        hw += MK.push_bar("Bar", 2.5, 13.5, 9.5, RECESS, tex="dp-steel", bar_tex="dp-steel", depth=1.1)
        for i, y in enumerate((3, 8, 13)):
            hw.append(B(f"Hinge{i}", (POST, y, RECESS - 0.35), (POST + 1.6, y + 2, RECESS), "dp-iron", faces=("north", "east", "up", "down")))
    else:
        # a wired window in a steel bead, and the red EXIT plate over it
        hw += [B("BeadT", (4.5, 9.0, RECESS - 0.5), (11.5, 9.6, RECESS), "dp-steel", faces=("north", "up", "east", "west")),
               B("BeadB", (4.5, 3.0, RECESS - 0.5), (11.5, 3.6, RECESS), "dp-steel", faces=("north", "down", "east", "west")),
               B("BeadL", (4.5, 3.6, RECESS - 0.5), (5.1, 9.0, RECESS), "dp-steel", faces=("north", "east", "west")),
               B("BeadR", (10.9, 3.6, RECESS - 0.5), (11.5, 9.0, RECESS), "dp-steel", faces=("north", "east", "west")),
               B("Glass", (5.1, 3.6, RECESS - 0.25), (10.9, 9.0, RECESS - 0.2), "dp-exitglass", faces=("north",), uv=[0, 0, 5.8, 5.4]),
               B("PlateRim", (3.0, 10.0, RECESS - 0.75), (13.0, 13.5, RECESS - 0.25), "dp-steel", faces=("north", "up", "down", "east", "west")),
               B("Plate", (3.5, 10.5, RECESS - 0.85), (12.5, 13.0, RECESS - 0.75), "dp-exitplate", faces=("north",), uv=[0, 0, 9, 2.5])]
        # (the plate's lettering is its top-left 24 x 10 px of 12 x 5 units: show the part of it that fits)
        hw[-1]["faces"]["north"]["uv"] = [0, 0, 12, 5]
        for i, y in enumerate((3, 7, 12)):
            hw.append(B(f"Hinge{i}", (POST, y - 1, RECESS - 0.35), (POST + 1.6, y + 1, RECESS), "dp-iron", faces=("north", "east", "up", "down")))
    return els + turned(hw)


# ---------------- Kitchen door ----------------

def kitchen_door(upper):
    """Two swing leaves with a gap between, proud of a dark core: a stainless kick plate and push plates in the lower
    block, a porthole in each leaf in the upper, hinge barrels at the jambs."""
    leaf = "dp-kitleaf-" + ("upper" if upper else "lower")
    els = door_frame(upper, "dp-kitframe") + [B("Core", (POST, 0, POST), (16 - POST, 16, 16 - POST), {"all": "dp-kitgap"}, faces=ALL4 + (("up",) if upper else ()))]
    zl = RECESS - 0.55  # the leaves' faces
    hw = []
    for side, (xa, xb) in (("L", (POST + 0.1, 7.75)), ("R", (8.25, 16 - POST - 0.1))):
        for e in MK.bevelled_box(f"Leaf{side}", (xa, 0, zl), (xb, 16, RECESS), {"all": leaf, "north": leaf}, b=0.25):
            if upper:
                e["faces"].pop("up", None)  # (the head rail's own top is at the same height)
            hw.append(e)
    if not upper:
        for side, (xa, xb) in (("L", (POST + 0.1, 7.75)), ("R", (8.25, 16 - POST - 0.1))):
            hw += MK.kick_plate(f"Kick{side}", xa + 0.4, xb - 0.4, 0.4, 4.4, zl, tex="dp-kitkick", t=0.25)
        hw += [B("PushL", (5.2, 8, zl - 0.3), (7.2, 12, zl), "dp-kitkick", faces=("north", "up", "down", "east", "west")),
               B("PushR", (8.8, 8, zl - 0.3), (10.8, 12, zl), "dp-kitkick", faces=("north", "up", "down", "east", "west"))]
        for side, x in (("L", POST), ("R", 16 - POST)):
            for i, y in enumerate((2, 7, 12)):
                hw.append(B(f"Barrel{side}{i}", (x - 0.4, y, zl - 0.45), (x + 0.4, y + 2.2, zl), "dp-iron"))
    else:
        for side, cx in (("L", 4.6), ("R", 11.4)):
            x1, x2, y1, y2 = cx - 2.4, cx + 2.4, 5.2, 12.0
            hw += [B(f"Ring{side}T", (x1, y2 - 0.45, zl - 0.45), (x2, y2, zl), "dp-steel", faces=("north", "up", "east", "west")),
                   B(f"Ring{side}B", (x1, y1, zl - 0.45), (x2, y1 + 0.45, zl), "dp-steel", faces=("north", "down", "east", "west")),
                   B(f"Ring{side}L", (x1, y1 + 0.45, zl - 0.45), (x1 + 0.45, y2 - 0.45, zl), "dp-steel", faces=("north", "east", "west")),
                   B(f"Ring{side}R", (x2 - 0.45, y1 + 0.45, zl - 0.45), (x2, y2 - 0.45, zl), "dp-steel", faces=("north", "east", "west")),
                   B(f"Glass{side}", (x1 + 0.45, y1 + 0.45, zl - 0.1), (x2 - 0.45, y2 - 0.45, zl - 0.05), "dp-kitglass",
                     faces=("north",), uv=[0, 0, 4, 5.5])]
        hw += [B("TopL", (POST + 0.1, 13.8, zl - 0.3), (7.75, 14.3, zl), "dp-kitkick", faces=("north", "up", "east", "west")),
               B("TopR", (8.25, 13.8, zl - 0.3), (16 - POST - 0.1, 14.3, zl), "dp-kitkick", faces=("north", "up", "east", "west"))]
    return els + turned(hw)


# ---------------- Level 9: the tool shelf ----------------

def hang(name, x, y, w, h, tex, z0, t=0.7, faces=("north", "up", "east", "west", "down")):
    return B(name, (x, y, z0 - t), (x + w, y + h, z0), tex, faces=faces)


def tool_shelf():
    """Steel shelving 15 x 28 units: two uprights, a pegboard back, a top, middle and bottom board, a red toolbox and
    two tins below, a box of nails, tins and a coil of rope on the middle board, and hung on the pegboard a hammer,
    a handsaw, a spanner and pliers, a row of screwdrivers and a hacksaw. Front to the north; the back is the wall."""
    zb = 15.4  # the pegboard's face
    s = "dp-shelfsteel"
    els = [B("UpL", (0.5, 0, 9), (1.5, 28, 16), s), B("UpR", (14.5, 0, 9), (15.5, 28, 16), s),
           B("Back", (1.5, 6.5, zb), (14.5, 27.2, 16), "dp-pegboard", faces=("north", "east", "west", "up", "down")),
           B("BackLow", (1.5, 0.8, 15.9), (14.5, 6.5, 16), s, faces=("north",)),
           B("Top", (0.5, 27.2, 9), (15.5, 28, 16), s),
           B("Mid", (1.5, 6.5, 9.5), (14.5, 7.2, 15.4), s),
           B("Low", (1.5, 0.8, 9.5), (14.5, 1.4, 15.9), s),
           B("LipMid", (1.5, 7.2, 9.5), (14.5, 7.9, 10.1), s, faces=("north", "up", "east", "west")),
           B("LipLow", (1.5, 1.4, 9.5), (14.5, 2.1, 10.1), s, faces=("north", "up", "east", "west"))]
    # bottom board: toolbox, two tins
    els += [B("Box", (2.2, 1.4, 10.6), (8.6, 5.4, 14.6), "dp-toolred"),
            B("BoxLid", (2.0, 5.4, 10.4), (8.8, 5.9, 14.8), "dp-toolred", faces=("north", "up", "east", "west", "south")),
            B("BoxHandle", (4.6, 5.9, 12.2), (6.2, 6.3, 12.8), "dp-toolblack"),
            B("TinA", (10.0, 1.4, 11.0), (12.2, 4.6, 13.2), "dp-tinred"), B("TinALid", (9.9, 4.6, 10.9), (12.3, 4.9, 13.3), "dp-steel"),
            B("TinB", (12.6, 1.4, 11.4), (14.2, 5.6, 13.6), "dp-tinblue"), B("TinBLid", (12.5, 5.6, 11.3), (14.3, 5.9, 13.7), "dp-steel")]
    # middle board: a box of nails, tins, a coil of rope
    els += [B("Nails", (2.2, 7.9, 11.0), (6.0, 10.4, 14.2), "dp-cardlabel", faces=("north", "east", "west", "up", "south")),
            B("TinC", (7.0, 7.9, 11.4), (9.0, 10.5, 13.4), "dp-tinblue"), B("TinCLid", (6.9, 10.5, 11.3), (9.1, 10.8, 13.5), "dp-steel"),
            B("TinD", (9.4, 7.9, 11.0), (11.6, 11.3, 13.2), "dp-tinred"), B("TinDLid", (9.3, 11.3, 10.9), (11.7, 11.6, 13.3), "dp-steel")]
    for i, (x, w, h) in enumerate(((12.0, 2.0, 2.0),)):
        els.append(B("Coil", (x, 7.9, 11.4), (x + w + 0.4, 7.9 + h + 0.6, 14.0), "dp-rope", faces=("north", "east", "west", "up")))
    # hung on the pegboard (z from its face outward)
    wood, steel, red, black, yellow = "dp-toolwood", "dp-toolsteel", "dp-toolred", "dp-toolblack", "dp-toolyellow"
    els += [hang("HammerH", 3.2, 12.0, 0.9, 9.5, wood, zb, 0.8),
            hang("HammerHead", 2.1, 21.2, 3.2, 1.5, steel, zb, 1.1), hang("HammerClaw", 1.5, 21.4, 0.8, 1.0, steel, zb, 0.9),
            hang("HammerFace", 5.3, 21.4, 0.6, 1.1, steel, zb, 1.1),
            hang("SawBlade", 6.8, 17.0, 4.2, 5.5, steel, zb, 0.35), hang("SawBlade2", 6.8, 13.5, 3.2, 3.5, steel, zb, 0.35),
            hang("SawBlade3", 6.8, 11.5, 2.2, 2.0, steel, zb, 0.35), hang("SawEdge", 6.8, 11.5, 0.5, 11.0, steel, zb, 0.5),
            hang("SawTeeth", 6.4, 11.5, 0.4, 11.0, "dp-toolblack", zb, 0.3),
            hang("SawGrip", 6.5, 22.2, 5.0, 1.0, wood, zb, 1.0), hang("SawGripL", 6.5, 22.2, 1.0, 3.5, wood, zb, 1.0),
            hang("SawGripR", 10.5, 22.2, 1.0, 3.5, wood, zb, 1.0),
            hang("SpannerH", 12.2, 10.5, 1.0, 8.5, steel, zb, 0.6), hang("SpannerJaw", 11.6, 19.0, 2.2, 2.4, steel, zb, 0.6),
            hang("SpannerJawB", 11.6, 21.4, 0.8, 1.6, steel, zb, 0.6),
            hang("Pliers", 2.4, 23.4, 1.1, 3.0, yellow, zb, 0.8), hang("PliersB", 3.4, 23.4, 1.1, 3.0, yellow, zb, 0.8),
            hang("PliersHead", 2.6, 26.1, 1.7, 0.9, steel, zb, 0.9),
            hang("Hack", 5.0, 25.6, 8.5, 0.6, steel, zb, 0.5), hang("HackGrip", 13.2, 24.5, 1.6, 2.2, red, zb, 1.2),
            hang("HackBar", 4.4, 24.8, 0.6, 1.5, steel, zb, 0.5)]
    return els


# ---------------- Level 10: the tool rack ----------------

def tool_rack():
    """A rack of three planks across two cleats against the wall, and four tools hung from it by iron straps: a spade,
    a pitchfork, a hoe and a rake. Front to the north; the board is at the wall."""
    zb = 14.0
    r, hnd, st = "dp-rackwood", "dp-handle", "dp-toolsteel"
    els = [B("Board", (0, 4, 14), (16, 26, 16), r, faces=("north", "east", "west", "up", "down")),
           B("CleatT", (0.5, 21.5, 13.2), (15.5, 23.3, 14), r, faces=("north", "east", "west", "up", "down")),
           B("CleatB", (0.5, 7.5, 13.2), (15.5, 9.3, 14), r, faces=("north", "east", "west", "up", "down"))]
    # spade
    def tool(x, ytop, ybot):
        return B(f"Handle{x}", (x - 0.6, ybot, 12.0), (x + 0.6, ytop, 13.2), hnd, faces=("north", "east", "west", "up", "down"))
    els += [tool(3.0, 26.5, 8.0),
            B("SpadeTop", (1.6, 25.6, 11.8), (4.4, 26.8, 13.2), hnd, faces=("north", "up", "east", "west")),
            B("SpadeBlade", (1.4, 3.0, 11.9), (4.6, 9.0, 12.5), st), B("SpadeShoulder", (2.2, 8.4, 11.9), (3.8, 9.6, 13.1), st),
            B("SpadeEdge", (1.4, 3.0, 11.8), (4.6, 3.5, 12.6), st, faces=("north", "down", "east", "west"))]
    # pitchfork
    els += [tool(7.0, 27.0, 10.0),
            B("ForkBack", (5.4, 8.6, 11.9), (8.6, 10.0, 13.0), st), B("ForkSocket", (6.3, 9.8, 11.9), (7.7, 11.2, 13.0), st)]
    for i, x in enumerate((5.4, 6.7, 8.0)):
        els.append(B(f"Tine{i}", (x, 3.0, 12.1), (x + 0.6, 8.8, 12.8), st))
    # hoe
    els += [tool(11.0, 26.0, 6.0),
            B("HoeNeck", (10.2, 5.0, 11.6), (11.8, 6.4, 12.8), st),
            B("HoeBlade", (10.4, 3.2, 10.4), (13.6, 5.2, 11.8), st, rot=(0, 0, 0))]
    # rake
    els += [tool(14.4, 26.5, 8.4),
            B("RakeBar", (12.8, 7.2, 11.9), (16.0, 8.6, 13.0), st)]
    for i in range(5):
        els.append(B(f"Tooth{i}", (12.9 + i * 0.7, 5.2, 12.2), (13.3 + i * 0.7, 7.2, 12.7), st))
    # iron straps over the handles at the cleats
    for x in (3.0, 7.0, 11.0, 14.4):
        for y in (22.0, 8.6):
            if x == 11.0 and y == 8.6:
                continue
            if x in (7.0,) and y == 8.6:
                continue
            els += [B(f"Strap{x}{y}", (x - 0.9, y - 0.3, 11.6), (x + 0.9, y + 0.3, 12.0), "dp-iron", faces=("north", "up", "down", "east", "west"))]
    return els


# ---------------- Level 10: the barrel of nails ----------------

def nail_barrel():
    """A coopered barrel 12 across, bulging at the middle (three tiers of eight staves), four iron hoops, and a heap of
    nails above the rim with a few standing out of it."""
    cx = cz = 8.0
    els = []
    tiers = ((0.0, 3.5, 5.4), (3.5, 10.5, 6.0), (10.5, 14.0, 5.4))
    for i, (y1, y2, a) in enumerate(tiers):
        for k, e in enumerate(octo_plates(f"Stave{i}", cx, cz, a, y1, y2, "dp-barrel", scale=2.0, course=i, t=0.7)):
            out = next(iter(e["faces"]))
            inner = {"north": "south", "south": "north", "east": "west", "west": "east"}[out]
            e["faces"][inner] = dict(e["faces"][out])
            e["faces"]["up"] = {"texture": "#dp-barrelhead", "uv": [0, 0, 5, 0.7]}
            els.append(e)
    for k, y in enumerate((1.6, 5.0, 9.0, 12.6)):
        a = 6.0 if 4.0 < y < 10.0 else 5.4
        els += octagon(f"Hoop{k}", cx, cz, a + 0.25, y, y + 0.9, "dp-hoop", faces=("north", "east", "south", "west", "up", "down"), lift=0.01)
    els += octagon("Floor", cx, cz, 5.3, 0.0, 0.2, "dp-barrelhead", faces=("down",))
    els += octagon("Heap", cx, cz, 4.8, 8.0, 13.2, "dp-nails", faces=("north", "east", "south", "west", "up"), lift=0.01)
    els += octagon("Heap2", cx, cz, 3.4, 13.2, 14.6, "dp-nails", faces=("north", "east", "south", "west", "up"), lift=0.01)
    els += octagon("Heap3", cx, cz, 1.8, 14.6, 15.4, "dp-nails", faces=("north", "east", "south", "west", "up"), lift=0.01)
    for i, (x, z, h) in enumerate(((6.0, 7.0, 1.6), (9.5, 8.5, 1.2), (8.2, 9.8, 2.0), (7.4, 6.5, 1.0))):
        els.append(B(f"Nail{i}", (x, 15.2, z), (x + 0.5, 15.2 + h, z + 0.5), "dp-steel", faces=ALL4 + ("up",)))
    return els


# ---------------- Level 10: the feed trough ----------------

def feed_trough():
    """A plank trough 16 long, 8 wide: two side planks and a bottom, end boards, a rim board along the top, standing on
    two trestles; feed heaped along two thirds of it and rainwater in the rest. Front to the north."""
    pl, end, tm = "dp-troughplank", "dp-troughend", "dp-troughpost"
    z1, z2 = 4.0, 12.0
    els = [B("Front", (0, 3, z1), (16, 8, z1 + 0.9), pl, faces=ALL4 + ("up",)),
           B("Back", (0, 3, z2 - 0.9), (16, 8, z2), pl, faces=ALL4 + ("up",)),
           B("EndL", (0, 3, z1 + 0.9), (0.9, 8, z2 - 0.9), end, faces=("west", "up", "south", "north")),
           B("EndR", (15.1, 3, z1 + 0.9), (16, 8, z2 - 0.9), end, faces=("east", "up", "south", "north")),
           B("Bottom", (0.9, 3, z1 + 0.9), (15.1, 4, z2 - 0.9), pl, faces=("up", "down")),
           B("RimF", (0, 8, z1 - 0.4), (16, 8.6, z1 + 1.3), tm, faces=("north", "up", "east", "west", "south")),
           B("RimB", (0, 8, z2 - 1.3), (16, 8.6, z2 + 0.4), tm, faces=("north", "up", "east", "west", "south")),
           B("Brace1", (4.5, 3, z1 - 0.3), (5.3, 7.4, z1), tm, faces=("north", "east", "west", "up")),
           B("Brace2", (10.7, 3, z1 - 0.3), (11.5, 7.4, z1), tm, faces=("north", "east", "west", "up"))]
    # trestle legs: a pair under each end, braced
    for i, x in enumerate((1.4, 12.6)):
        els += [B(f"LegA{i}", (x, 0, z1 + 0.4), (x + 1.4, 3, z1 + 1.8), tm), B(f"LegB{i}", (x, 0, z2 - 1.8), (x + 1.4, 3, z2 - 0.4), tm),
                B(f"Cross{i}", (x, 1.2, z1 + 1.8), (x + 1.4, 1.9, z2 - 1.8), tm, faces=("up", "down", "east", "west"))]
    # contents: feed and straw over the left two thirds, water over the rest
    els += [B("Feed", (1.0, 4, z1 + 1.0), (10.2, 6.6, z2 - 1.0), "dp-feed", faces=("up", "north", "south", "west", "east")),
            B("FeedTop", (2.0, 6.6, z1 + 1.6), (8.6, 7.4, z2 - 1.6), "dp-feed", faces=("up", "north", "south", "west", "east")),
            B("Hay", (3.4, 7.4, 5.8), (6.6, 7.9, 9.6), "dp-hay", faces=("up", "north", "south", "west", "east")),
            B("Water", (10.2, 4, z1 + 1.0), (15.0, 6.1, z2 - 1.0), "dp-troughwater", faces=("up",), uv=[0, 0, 4.8, 6])]
    els[-1]["faces"]["up"]["uv"] = [0, 0, 4.8, 6.0]
    els.append(B("WaterEdge", (10.2, 4, z1 + 1.0), (10.3, 6.1, z2 - 1.0), "dp-feed", faces=("east",)))
    return els


# ---------------- Level 10: the hand pump ----------------

def hand_pump():
    """A cast-iron pitcher pump: a stepped concrete plinth with bolted flange, an octagonal barrel, a collar, a domed
    head on two lugs, a spout with a lip on the north side, and a long handle pivoting on the head with a grip at its
    end, raised."""
    cx = cz = 8.0
    iron, paint, conc = "dp-pumpiron", "dp-pumphandle", "dp-pumpplinth"
    els = [B("Plinth", (3.5, 0, 3.5), (12.5, 1.8, 12.5), conc, faces=ALL4 + ("up",)),
           B("PlinthTop", (4.5, 1.8, 4.5), (11.5, 2.4, 11.5), "dp-pumpwet", faces=ALL4 + ("up",))]
    els += octagon("Flange", cx, cz, 3.4, 2.4, 3.4, iron, faces=ALL4 + ("up",), lift=0.01)
    for i, (x, z) in enumerate(((5.6, 5.6), (9.9, 5.6), (5.6, 9.9), (9.9, 9.9))):
        els.append(B(f"Bolt{i}", (x, 3.4, z), (x + 0.5, 3.9, z + 0.5), "dp-steel", faces=ALL4 + ("up",)))
    els += octagon("Barrel", cx, cz, 2.3, 3.4, 11.0, iron, faces=ALL4, lift=0.01)
    els += octagon("Collar", cx, cz, 2.9, 6.0, 7.0, iron, faces=ALL4 + ("up", "down"), lift=0.01)
    els += octagon("Neck", cx, cz, 2.9, 10.4, 11.6, iron, faces=ALL4 + ("down",), lift=0.01)
    els += octagon("Head", cx, cz, 2.2, 11.6, 14.2, iron, faces=ALL4, lift=0.01)
    els += octagon("Dome", cx, cz, 1.4, 14.2, 15.2, iron, faces=ALL4 + ("up",), lift=0.01)
    # spout: a tapering run out to the north, sloping down a little, with a lip
    els += [B("Spout", (7.2, 8.6, 1.6), (8.8, 10.2, 6.0), iron, faces=ALL4 + ("up", "down"), rot=(-8, 0, 0), origin=(8, 9.4, 6)),
            B("SpoutLip", (6.9, 8.0, 0.9), (9.1, 9.0, 2.0), iron, faces=ALL4 + ("up", "down"), rot=(-8, 0, 0), origin=(8, 9.4, 6)),
            B("Drip", (7.4, 7.6, 1.3), (8.6, 8.0, 1.8), "dp-troughwater", faces=("down",))]
    # pivot lugs and handle
    els += [B("LugL", (6.2, 13.6, 6.8), (7.0, 16.6, 9.8), iron, faces=ALL4 + ("up",)),
            B("LugR", (9.0, 13.6, 6.8), (9.8, 16.6, 9.8), iron, faces=ALL4 + ("up",)),
            B("Pin", (6.0, 15.4, 8.0), (10.0, 16.0, 8.6), "dp-steel", faces=("north", "up", "east", "west"))]
    els += [B("Handle", (7.35, 15.2, 8.0), (8.65, 16.2, 17.5), paint, faces=ALL4 + ("up", "down"), rot=(-32, 0, 0), origin=(8, 15.7, 8.3)),
            B("Weight", (7.0, 14.6, 5.4), (9.0, 16.6, 7.6), paint, faces=ALL4 + ("up", "down"), rot=(-32, 0, 0), origin=(8, 15.7, 8.3)),
            B("Grip", (7.1, 15.0, 17.5), (8.9, 16.4, 21.0), "dp-toolwood", faces=ALL4 + ("up", "down"), rot=(-32, 0, 0), origin=(8, 15.7, 8.3))]
    return els
