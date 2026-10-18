"""Level 4's props as geometry (graphics pass, "Level 4 art"), built with tools/modelkit.py: the dead ficus, reception
desk, coat stand, stacked chairs, wall clock, office door, drinking fountain and the shut window. Each function returns
shape elements in `detail_kit.bx`'s format; `gen_detail.level4` puts them into the props, wall decorations, door and
window blocks. The textures are in `l4props_tex`.

Wall decorations are modelled on a wall's north face: z < 0 is out of the wall, z = 0 the wall. Free props stand in a
block, their front to the north. Rotations: an element's rotation is applied as Rx, Ry, Rz in the game's order about its
origin (see check_zfight), so a limb or a leaf that must droop and then turn about the vertical is built along +x or +y,
tilted with rotationZ first and turned with rotationY.
"""
import math
import random

import modelkit as K
from detail_kit import seed_of
from gen_shapes import octagon

mat = K.mat
DIRS = K.DIRS
SIDES4 = ("north", "east", "south", "west")
NOSOUTH = ("north", "east", "west", "up", "down")


def b(name, frm, to, tex, faces=DIRS, **kw):
    return K.box(name, frm, to, tex, faces=faces, **kw)


def _rz(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return lambda p: (c * p[0] - s * p[1], s * p[0] + c * p[1], p[2])


def _ry(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return lambda p: (c * p[0] + s * p[2], p[1], -s * p[0] + c * p[2])


# ======================= The dead ficus =======================

def ficus():
    """A dead rubber plant in a cream ceramic pot with a saucer and dry cracked soil: a trunk in three leaning lengths,
    branches and twigs of real round-ish limbs (square sections, tapering), dry leaves (each a thin blade, drooping, in
    six tones), a few bare tips, and leaves fallen on the soil and the floor. Footprint as before (0.3-0.7, to 1.8)."""
    rng = random.Random(seed_of("l4ficus"))
    els = [b("Saucer", (4.4, 0, 4.4), (11.6, 0.6, 11.6), "l4pot"),
           b("PotFoot", (5.3, 0.6, 5.3), (10.7, 2.4, 10.7), "l4pot"),
           b("PotBody", (4.9, 2.4, 4.9), (11.1, 6.5, 11.1), "l4pot"),
           b("RimN", (4.6, 6.5, 4.6), (11.4, 7.5, 5.4), "l4pot", faces=DIRS),
           b("RimS", (4.6, 6.5, 10.6), (11.4, 7.5, 11.4), "l4pot"),
           b("RimW", (4.6, 6.5, 5.4), (5.4, 7.5, 10.6), "l4pot", faces=("north", "south", "east", "west", "up")),
           b("RimE", (10.6, 6.5, 5.4), (11.4, 7.5, 10.6), "l4pot", faces=("north", "south", "east", "west", "up")),
           b("Soil", (5.4, 6.5, 5.4), (10.6, 7.05, 10.6), "l4soil", faces=("up",))]

    def limb(name, base, length, tilt, yaw, t):
        """A square limb from `base` along its tilt and yaw (degrees from vertical, then turned about the vertical);
        returns the end point."""
        x, y, z = base
        els.append(b(name, (x - t / 2, y, z - t / 2), (x + t / 2, y + length, z + t / 2), "l4bark",
                     faces=("north", "east", "south", "west", "up"), rot=(0, yaw, -tilt), origin=base))
        p = _ry(yaw)(_rz(-tilt)((0, length, 0)))
        return (x + p[0], y + p[1], z + p[2])

    leaf_i = [0]

    def leaf(base, yaw, droop, size=1.0):
        x, y, z = base
        ln, w = 2.6 * size, 1.4 * size
        end = _ry(yaw)(_rz(-droop)((ln, 0, 0)))
        ex, ey, ez = x + end[0], y + end[1], z + end[2]
        if not (0.4 < ex < 15.6 and 0.4 < ez < 15.6 and ey > 0.3):
            return
        i = leaf_i[0]
        leaf_i[0] += 1
        els.append(b(f"Leaf{i}", (x, y - 0.1, z - w / 2), (x + ln, y + 0.1, z + w / 2), f"l4leaf{rng.randrange(6)}",
                     rot=(0, yaw, -droop), origin=base))

    def leaves(base, n, droop=(20, 75)):
        for k in range(n):
            leaf(base, rng.uniform(0, 360), rng.uniform(*droop), rng.uniform(0.8, 1.15))

    # trunk: three leaning lengths
    p0 = (8, 7.0, 8)
    p1 = limb("Trunk1", p0, 7.5, 4, 70, 1.5)
    p2 = limb("Trunk2", p1, 6.5, -5, 70, 1.2)
    p3 = limb("Trunk3", p2, 5.5, 6, 70, 0.95)
    tips = [p3]
    # branches off the nodes, each carrying a twig or two
    for i, (node, tilt, yaw, ln, t) in enumerate((
            (p1, 52, 15, 4.2, 0.85), (p1, 50, 200, 3.8, 0.8), (p2, 46, 100, 3.6, 0.8), (p2, 55, 290, 3.4, 0.75),
            (p3, 32, 40, 2.8, 0.6), (p3, 38, 215, 2.6, 0.6))):
        end = limb(f"Branch{i}", node, ln, tilt, yaw, t)
        leaves((node[0] + (end[0] - node[0]) * 0.6, node[1] + (end[1] - node[1]) * 0.6, node[2] + (end[2] - node[2]) * 0.6), 3)
        for j, (dt, dy, tl) in enumerate(((22, 50, 2.0), (-20, -55, 1.7))):
            if i % 3 == 2 and j == 1:
                continue
            tw = limb(f"Twig{i}{j}", end, tl, tilt + dt, yaw + dy, 0.5)
            tips.append(tw)
        tips.append(end)
    # the dry foliage: most tips keep a few leaves, two are bare sticks
    for i, tip in enumerate(tips):
        if i in (3, 9):
            continue
        leaves(tip, rng.randint(5, 8))
    # fallen leaves on the soil and the floor
    for i, (x, z, ry) in enumerate(((6.4, 6.6, 20), (9.6, 9.2, 150), (7.2, 9.4, 80))):
        els.append(b(f"SoilLeaf{i}", (x, 7.05, z), (x + 2.0, 7.2, z + 1.1), f"l4leaf{(i * 2) % 6}", rot=(0, ry, 0)))
    for i, (x, z, ry) in enumerate(((2.2, 10.5, 30), (11.4, 3.3, 110), (12.6, 11.5, 60), (3.4, 4.2, 140), (8.4, 13.0, 10))):
        els.append(b(f"FloorLeaf{i}", (x, 0.02, z), (x + 2.2, 0.22, z + 1.2), f"l4leaf{(i + 1) % 6}", rot=(0, ry, 0)))
    return els


# ======================= The reception desk =======================

def reception_desk():
    """A counter run of 1-block pieces that join (x 0-16), facing north: a veneered fascia with a raised panel and a
    bead, a kick, a tall transaction ledge with a dark edge banding and overhang over a lower worktop, a brass plate,
    a modesty panel and on the staff side a drawer pedestal with pulls, the old terminal and a ledger on the worktop."""
    els = [b("Kick", (0, 0, 3.5), (16, 1.5, 14), "l4kick", faces=("north", "south", "east", "west")),
           b("Fascia", (0, 1.5, 3.5), (16, 16.5, 5), "l4veneer", faces=("north", "east", "west", "up", "down")),
           b("Ledge", (0, 16.5, 1.5), (16, 17.5, 6.5), mat(top="l4counter", side="l4edge", bottom="l4edge")),
           b("LedgeBack", (0, 16.5, 5), (16, 17, 6.5), "l4edge", faces=("south", "east", "west"))]
    # fielded panel on the fascia: a raised bead round a recessed panel
    frame, openings = K.frame_members("Bead", 1.5, 3.2, 14.5, 15.2, 2.9, 3.5, 0.6, "l4veneer")
    for e in frame:
        e["faces"].pop("south", None)
    els += frame
    els.append(b("Panel", (2.1, 3.8, 3.2), (13.9, 14.6, 3.5), "l4veneer", faces=("north",)))
    els.append(b("Plate", (1.0, 15.2, 2.7), (15.0, 16.2, 2.95), "l4recplate", faces=("north",), uv=[0, 0, 16, 2.4]))
    # worktop behind, modesty panel, drawer pedestal on the staff side
    els += [b("Worktop", (0, 11.5, 5), (16, 12.5, 15), "l4counter"),
            b("Modesty", (0, 3, 13.6), (16, 11.5, 14.2), "l4veneer", faces=("north", "south", "east", "west", "down")),
            b("Pedestal", (1, 1.5, 7.5), (8, 11.5, 13.6), "l4veneer", faces=("north", "south", "east", "west", "down"))]
    for i, (y1, y2) in enumerate(((2.0, 6.0), (6.5, 10.9))):
        els += K.bevelled_box(f"Drawer{i}", (1.4, y1, 13.6), (7.6, y2, 14.2), "l4veneer", b=0.25)
        els.append(b(f"Pull{i}", (3.6, (y1 + y2) / 2 + 0.7, 14.2), (5.4, (y1 + y2) / 2 + 1.2, 14.9), "metal"))
    els.append(b("Ledger", (11, 12.5, 7.5), (14.6, 12.9, 11.5), "l4ledger", faces=("up", "north", "south", "east", "west")))
    els.append(b("Pen", (10.2, 12.5, 7.8), (10.7, 12.9, 10.8), "l4kick", faces=("up", "north", "south", "east", "west")))
    return els


# ======================= The coat stand =======================

def coat_stand():
    """A turned wooden stand: a stepped octagonal foot, a pole with a collar and a finial, two tiers of up-curved hooks
    (four on top, four turned half a step below, each with a knob), with a wool coat on a hanger over the east top hook
    and a scarf on the west one."""
    els = octagon("Foot", 8, 8, 4.2, 0, 0.9, "l4stand", faces=SIDES4 + ("up",), lift=0.01)
    els += octagon("Foot2", 8, 8, 3.0, 0.9, 2.2, "l4stand", faces=SIDES4 + ("up",), lift=0.01)
    els += [b("Pole", (7.5, 2.2, 7.5), (8.5, 27.4, 8.5), "l4stand", faces=SIDES4)]
    els += octagon("Collar", 8, 8, 1.1, 11.5, 12.7, "l4stand", faces=SIDES4 + ("up", "down"), lift=0.01)
    els += octagon("Neck", 8, 8, 1.0, 26.4, 27.4, "l4stand", faces=SIDES4 + ("up", "down"), lift=0.01)
    els += octagon("Finial", 8, 8, 1.3, 27.4, 28.6, "l4stand", faces=SIDES4 + ("up",), lift=0.01)
    for tier, (y, ln, off) in enumerate(((24.2, 3.2, 0), (19.0, 2.6, 45))):
        for k in range(4):
            yaw = off + 90 * k
            o = (8, y, 8)
            els.append(b(f"Hook{tier}{k}", (8.4, y - 0.4, 7.55), (8.4 + ln, y + 0.4, 8.45), "l4stand", rot=(0, yaw, 30), origin=o))
            els.append(b(f"Knob{tier}{k}", (8.4 + ln - 0.2, y - 0.2, 7.3), (8.4 + ln + 1.1, y + 1.1, 8.7), "l4stand", rot=(0, yaw, 30), origin=o))
    # the coat on the east top hook: hanger, shoulders, body, sleeves, hem, collar, buttons
    cx = 11.25
    els += [b("HangerNeck", (cx - 0.25, 23.4, 7.65), (cx + 0.25, 25.2, 8.35), "l4hanger"),
            b("HangerBar", (cx - 0.3, 22.5, 5.4), (cx + 0.3, 23.2, 10.6), "l4hanger"),
            b("CoatShoulder", (cx - 1.0, 20.2, 5.2), (cx + 0.9, 22.5, 10.8), "l4coat"),
            b("CoatBody", (cx - 1.1, 9.6, 5.5), (cx + 1.0, 20.2, 10.5), "l4coat"),
            b("CoatHem", (cx - 1.3, 7.6, 5.3), (cx + 1.2, 9.6, 10.7), "l4coat"),
            b("SleeveN", (cx - 0.9, 10.8, 4.5), (cx + 0.8, 21.4, 5.4), "l4coat"),
            b("SleeveS", (cx - 0.9, 10.8, 10.6), (cx + 0.8, 21.4, 11.5), "l4coat"),
            b("Collar", (cx - 1.1, 22.0, 6.2), (cx + 1.0, 23.0, 9.8), "l4coat"),
            b("Lining", (cx - 1.1, 7.6, 7.9), (cx - 1.0, 9.6, 8.1), "l4lining", faces=("west",))]
    for i, y in enumerate((11.5, 14.8, 18.0)):
        els.append(b(f"Button{i}", (cx + 1.0, y, 7.6), (cx + 1.35, y + 0.7, 8.4), "l4button"))
    # a scarf over the west top hook, ends hanging to different lengths
    els += [b("ScarfTop", (4.4, 24.5, 7.3), (5.6, 25.4, 8.7), "l4scarf"),
            b("ScarfEndA", (4.5, 17.5, 7.2), (5.4, 24.5, 8.2), "l4scarf"),
            b("ScarfEndB", (4.5, 19.5, 8.2), (5.4, 24.5, 8.9), "l4scarf")]
    return els


# ======================= Stacked chairs =======================

def chair_stack():
    """Five stackable plastic chairs, stacked: each moulded seat sits 2.4 above the one below and a little forward, so
    its rear edge clears the lower one's back; the seat shell, a back with a slot, four tubular legs (the bottom chair's
    to the floor with rubber feet, the others' short stubs standing on the seat below)."""
    els = []
    rng = random.Random(seed_of("l4chairs"))
    n = 5
    for i in range(n):
        y0 = i * 2.3
        dz = -0.9 * i
        dx = rng.uniform(-0.45, 0.45)
        x1, x2 = 3.5 + dx, 12.5 + dx
        seat_y = y0 + 6.4
        els.append(b(f"Seat{i}", (x1, seat_y, 4.8 + dz), (x2, seat_y + 1.0, 13.8 + dz), "l4shell"))
        els.append(b(f"SeatLip{i}", (x1, seat_y + 1.0, 4.8 + dz), (x2, seat_y + 1.5, 5.6 + dz), "l4shell", faces=DIRS))
        for k, (lx, lz) in enumerate(((x1 + 0.7, 5.4 + dz), (x2 - 1.5, 5.4 + dz), (x1 + 0.7, 12.2 + dz), (x2 - 1.5, 12.2 + dz))):
            lo = 0.5 if i == 0 else seat_y - 1.4
            els.append(b(f"Leg{i}{k}", (lx, lo, lz), (lx + 0.8, seat_y, lz + 0.8), "l4tube", faces=SIDES4))
            if i == 0:
                els.append(b(f"Foot{i}{k}", (lx - 0.1, 0, lz - 0.1), (lx + 0.9, 0.5, lz + 0.9), "l4foot"))
        # the back leans 8 degrees: lower panel, two uprights with a slot between, top bar (its own origin at the base)
        bz = 12.9 + dz
        org = (8 + dx, seat_y + 1.0, bz)
        by = seat_y + 1.0
        for nm, (xa, xb, ya, yb) in (("Lo", (x1 + 0.4, x2 - 0.4, 0, 3.6)), ("Top", (x1 + 0.4, x2 - 0.4, 5.6, 7.4)),
                                     ("PostL", (x1 + 0.4, x1 + 1.8, 3.6, 5.6)), ("PostR", (x2 - 1.8, x2 - 0.4, 3.6, 5.6))):
            els.append(b(f"Back{nm}{i}", (xa, by + ya, bz), (xb, by + yb, bz + 0.9), "l4shell", rot=(8, 0, 0), origin=org))
    return els


# ======================= The wall clock =======================

def wall_clock():
    """A square-cased wall clock with a round dial: a black bezel frame (rounded by its steps) round a dial printed in the
    pixel face (12, 3, 6, 9 and sixty ticks), glass in front (a cut-out with a few glints), an hour and a minute hand and a
    centre cap as geometry, stopped at 3:14."""
    x1, y1, x2, y2 = 3.5, 3.5, 12.5, 12.5
    frame, _ = K.frame_members("Case", x1, y1, x2, y2, -1.9, 0, 1.0, "l4clockcase")
    for e in frame:
        e["faces"].pop("south", None)
    els = list(frame)
    els.append(b("Dial", (x1 + 1.0, y1 + 1.0, -1.35), (x2 - 1.0, y2 - 1.0, -1.2), "l4clockface", faces=("north",), uv=[0, 0, 16, 16]))
    els.append(b("Glass", (x1 + 1.0, y1 + 1.0, -1.7), (x2 - 1.0, y2 - 1.0, -1.65), "l4clockglass", faces=("north",), uv=[0, 0, 16, 16]))
    cx, cy = 8.0, 8.0
    els.append(b("HourHand", (cx - 0.3, cy - 0.5, -1.56), (cx + 0.3, cy + 2.0, -1.5), "l4clockcase", faces=("north", "east", "west", "up"),
                 rot=(0, 0, 97), origin=(cx, cy, -1.5)))
    els.append(b("MinuteHand", (cx - 0.2, cy - 0.6, -1.62), (cx + 0.2, cy + 3.1, -1.56), "l4clockcase", faces=("north", "east", "west", "up"),
                 rot=(0, 0, 84), origin=(cx, cy, -1.56)))
    els.append(b("Cap", (cx - 0.45, cy - 0.45, -1.66), (cx + 0.45, cy + 0.45, -1.62), "l4clockcase", faces=("north", "east", "west", "up", "down")))
    return els


# ======================= The drinking fountain =======================

def fountain():
    """A wall-hung stainless drinking fountain at a real height: the bowl's rim 14.2/16 up (0.89 m), the bubbler's head at
    15.6/16 (0.975 m), as a wall-hung unit stands in an office. A backsplash plate to the top of the block, a bowl of a
    rim, a dished floor with its drain, a tapered shell and trap under it, a gooseneck bubbler, and a push button."""
    s = "l4fsteel"
    els = [b("Back", (2.5, 9.5, -0.6), (13.5, 15.75, 0), s, faces=("north", "east", "west", "up")),
           b("RimF", (2.5, 13.2, -7.0), (13.5, 14.2, -6.0), s), b("RimL", (2.5, 13.2, -6.0), (3.5, 14.2, -0.6), s),
           b("RimR", (12.5, 13.2, -6.0), (13.5, 14.2, -0.6), s), b("RimB", (3.5, 13.2, -1.6), (12.5, 14.2, -0.6), s),
           b("Dish", (3.5, 12.4, -6.0), (12.5, 13.5, -1.6), "l4fbowl", faces=("up",)),
           b("DishSides", (3.5, 12.4, -6.0), (12.5, 13.2, -1.6), s, faces=("north", "east", "west", "south", "down")),
           b("Drain", (6.9, 13.5, -4.4), (8.7, 13.55, -2.9), "l4fdrain", faces=("up",)),
           b("Shell", (3.9, 9.8, -5.6), (12.1, 12.4, -0.6), "l4fsteelv", faces=("north", "east", "west", "down")),
           b("Trap", (6.4, 8.2, -3.8), (9.6, 9.8, -0.6), "l4fsteelv", faces=("north", "east", "west", "down")),
           b("Neck", (7.4, 13.5, -1.5), (8.6, 15.0, -0.7), s, faces=SIDES4),
           b("Gooseneck", (7.5, 14.9, -3.4), (8.5, 15.5, -1.4), s),
           b("Head", (7.3, 14.5, -3.7), (8.7, 15.2, -2.9), "l4fblack"),
           b("Button", (11.1, 14.2, -3.9), (12.3, 14.7, -2.7), "l4fblack", faces=("up", "north", "south", "east", "west"))]
    return els


# ======================= The office door =======================

def office_door(part):
    """The locked office door's leaf (a veneer cube) with its hardware on all four sides (the block has no facing; on the
    two that meet the jambs it is buried in the wall): a steel frame round the leaf, a lever on a rose, a lock cylinder
    and a thumb-turn above it, a kick plate and two hinges on the lower; on the upper a vision strip of dark glass under a
    bead and the ROOM plate. Everything stops 0.05 short of the block's sides (B8's lesson)."""
    fr = "l4doorframe"
    hw = [b("StileL", (0.05, 0, -0.5), (1.55, 16, 0), fr, faces=("north", "east", "west") + (() if part == "upper" else ("down",))),
          b("StileR", (14.45, 0, -0.5), (15.95, 16, 0), fr, faces=("north", "east", "west") + (() if part == "upper" else ("down",)))]
    if part == "lower":
        hw.append(b("RailB", (1.55, 0, -0.5), (14.45, 1.2, 0), fr, faces=("north", "up")))
        hw += K.lever("Lever", 3.6, 8.6, 0, length=3.2, tex="l4lever", side=1)
        hw.append(b("LockPlate", (2.4, 10.4, -0.5), (4.8, 14.0, 0), "l4lockface", faces=NOSOUTH))
        hw.append(b("LockCyl", (3.1, 11.0, -0.9), (4.1, 12.0, -0.5), "brass", faces=NOSOUTH))
        hw.append(b("Turn", (3.35, 12.7, -0.9), (3.85, 13.6, -0.5), "l4lever", faces=NOSOUTH))
        hw += K.kick_plate("Kick", 2.5, 13.5, 1.5, 5.0, 0, tex="l4kickplate")
        hw += K.hinge("HingeA", 15.2, 2.5, 5.5, 0, tex="l4lever", side="right")
        hw += K.hinge("HingeB", 15.2, 10.0, 13.0, 0, tex="l4lever", side="right")
    else:
        hw.append(b("RailT", (1.55, 14.8, -0.5), (14.45, 16, 0), fr, faces=("north", "down")))
        bead, _ = K.frame_members("Bead", 5.0, 5.5, 11.0, 14.0, -0.6, 0, 0.5, fr)
        for e in bead:
            e["faces"].pop("south", None)
        hw += bead
        hw.append(b("Glass", (5.5, 6.0, -0.35), (10.5, 13.5, -0.2), "l4doorglass", faces=("north",)))
        hw.append(b("Plate", (4.0, 1.5, -0.5), (12.0, 5.0, 0), "l4roomplate", faces=NOSOUTH, uv=[0, 0, 16, 7]))
        hw += K.hinge("HingeA", 15.2, 10.0, 13.0, 0, tex="l4lever", side="right")
    els = [b("Leaf", (0, 0, 0), (16, 16, 16), f"officedoor-{part}", uv=[0, 0, 16, 16])]
    for i in range(4):
        els += [dict(e, name=f"{e['name']}{i}") for e in K.turn(_wall(hw), i)]
    return els


def _wall(els):
    for e in els:
        if e["to"][2] == 0 and "south" in e["faces"]:
            del e["faces"]["south"]
    return els


# ======================= The shut window =======================

def blackout_window():
    """A blacked-out window as a block with no facing: a satin-aluminium frame, the pane painted black and recessed 2
    units on all four sides (corner posts and rails round it, so a ribbon of them reads as framed panes with a
    mullion between and a transom across), strips of masking tape holding the edges. Nothing lies on the block's top or
    bottom plane (the rails' outer faces are left out) and the posts' outer ends stay in the block's own planes."""
    fr = "l4winframe"
    els = [b("RailB", (0, 0, 0), (16, 1.5, 16), fr, faces=SIDES4 + ("up",)),
           b("RailT", (0, 14.5, 0), (16, 16, 16), fr, faces=SIDES4 + ("down",))]
    for i, (x, z) in enumerate(((0, 0), (14, 0), (0, 14), (14, 14))):
        els.append(b(f"Post{i}", (x, 1.5, z), (x + 2, 14.5, z + 2), fr, faces=SIDES4))
    els.append(b("Pane", (2, 1.5, 2), (14, 14.5, 14), "l4blackpane", faces=SIDES4))
    for nm, frm, to, faces in (("TapeN", (2.8, 12.6, 1.75), (13.2, 13.9, 2.0), ("north", "up", "down")),
                               ("TapeS", (2.8, 12.6, 14.0), (13.2, 13.9, 14.25), ("south", "up", "down")),
                               ("TapeW", (1.75, 12.6, 2.8), (2.0, 13.9, 13.2), ("west", "up", "down")),
                               ("TapeE", (14.0, 12.6, 2.8), (14.25, 13.9, 13.2), ("east", "up", "down"))):
        els.append(b(nm, frm, to, "l4tape", faces=faces))
    return els


def glass_partition():
    """The conference-room glass: one pane, but inset 0.05 from the block's top and bottom planes (it lay exactly on the
    carpet's top and the ceiling tile's underside, and the two shimmered against each other), with no top or bottom
    faces at all."""
    return [b("Glass", (0, 0.05, 0), (16, 15.95, 16), "officeglass", faces=SIDES4, uv=[0, 0, 16, 16])]
