"""Level 5's props as geometry (graphics pass, "Level 5 art"), built with tools/modelkit.py: the furnace, curio cabinet,
ice machine, nightstand, bed (head and foot halves), grandfather clock and gilt mirror. Each function returns shape
elements in `detail_kit.bx`'s format. The textures are in `l5props_tex`.

Free props stand in a block with their front to the north (low z); wall decorations are modelled on a wall's north
face (z < 0 is out of the wall). Codes, footprints and collision boxes are the old ones (gen_blocktypes, gen_detail).
"""
import math

import modelkit as K

DIRS = K.DIRS
NOS = ("north", "east", "west", "up", "down")           # a part against a face behind it: no south
NOD = ("north", "east", "south", "west", "up")          # a part standing on something: no underside


def b(name, frm, to, tex, faces=DIRS, **kw):
    return K.box(name, frm, to, tex, faces=faces, **kw)


def _octagon():
    from gen_shapes import octagon  # lazily: gen_shapes imports this module
    return octagon


# ======================= Furnace =======================

def furnace():
    """A cast-iron furnace, front to the north (shared with the boiler's riveted plate, band, strap and flue textures): a
    plinth, a body of riveted plates with two strap bands round its sides and back, a hood in two steps with a flue
    collar and a short stack, and on the front a firebox door: the glowing window (unchanged: 4-12, 2-9, 1.6 deep) in a
    heavy frame with rivets, hinges and a latch, and over it a small ash-pit door with a pull. Same footprint as before
    (body 1-15 x 2-15, hood 0-16 x 1-16)."""
    octagon = _octagon()
    els = [b("Plinth", (0.5, 0, 1.0), (15.5, 1.5, 15.5), "band", faces=NOD),
           b("Body", (1, 1.5, 2), (15, 14, 15), "shell", faces=("north", "east", "south", "west", "up"))]
    # the firebox door's frame: sill, lintel and two stiles round the window (4-12, 2-9), standing out to z 1
    fz1, fz2 = 1.0, 2.0
    els += [b("FrameSill", (2.5, 1.5, fz1), (13.5, 2.0, fz2), "l5castiron", faces=("north", "east", "west", "up")),
            b("FrameHead", (2.5, 9.0, fz1), (13.5, 10.5, fz2), "l5castiron"),
            b("FrameL", (2.5, 2.0, fz1), (4.0, 9.0, fz2), "l5castiron", faces=("north", "east", "west")),
            b("FrameR", (12.0, 2.0, fz1), (13.5, 9.0, fz2), "l5castiron", faces=("north", "east", "west"))]
    els.append(b("Window", (4, 2, 1.6), (12, 9, 2), "fire", glow=200, faces=("north",)))
    for i, (x, y) in enumerate(((3.25, 9.75), (12.75, 9.75), (3.25, 2.6), (12.75, 2.6))):
        els.append(b(f"Rivet{i}", (x - 0.4, y - 0.4, 0.6), (x + 0.4, y + 0.4, fz1), "l5castiron", faces=("north", "east", "west", "up", "down")))
    els += K.hinge("Hinge1", 2.5, 3.5, 5.5, fz1, tex="l5castiron", side="left")
    els += K.hinge("Hinge2", 2.5, 6.0, 8.0, fz1, tex="l5castiron", side="left")
    els += K.handle("Latch", 12.75, 6.0, fz1, length=3.0, axis="y", standoff=0.7, thick=0.6, tex="l5castiron")
    # the ash-pit door over it
    els += K.bevelled_box("Ash", (4.5, 10.9, 1.3), (11.5, 13.4, 2.0), "l5castiron", b=0.25)
    els += K.handle("AshPull", 8.0, 12.15, 1.3, length=2.5, axis="x", standoff=0.5, thick=0.5, tex="l5castiron")
    # strap bands round the sides and the back (the front has the door), each a row of rivets
    for k, (y1, y2) in enumerate(((3.0, 5.0), (9.0, 11.0))):
        els += [b(f"BandE{k}", (15.0, y1, 2.0), (15.3, y2, 15.0), "strap", faces=("north", "east", "south", "up", "down")),
                b(f"BandW{k}", (0.7, y1, 2.0), (1.0, y2, 15.0), "strap", faces=("north", "west", "south", "up", "down")),
                b(f"BandB{k}", (1.0, y1, 15.0), (15.0, y2, 15.3), "strap", faces=("east", "south", "west", "up", "down"))]
    # the hood: two steps, then the collar and a short stack (the blocktype's smoke leaves the top)
    els += [b("HoodLo", (0.25, 14, 1.25), (15.75, 15, 15.75), "band"),
            b("HoodHi", (2.0, 15, 3.0), (14.0, 16, 14.0), "band", faces=NOD)]
    els += octagon("Collar", 8, 8.5, 2.6, 16, 16.8, "band", faces=("north", "east", "south", "west", "up"), lift=0.01)
    els += octagon("Stack", 8, 8.5, 1.9, 16.8, 19.0, "flue", faces=("north", "east", "south", "west"))
    els += octagon("StackLip", 8, 8.5, 2.2, 19.0, 19.6, "band", faces=("north", "east", "south", "west", "up", "down"), lift=0.01)
    return els


# ======================= Curio cabinet =======================

def curio_cabinet():
    """A glazed mahogany display cabinet, two blocks tall and half a block deep (front at z 7.6): a plinth with a foot
    moulding, sides, a velvet-lined back, glass shelves, and on them small curios (a cobalt vase, china plates on edge,
    brass candlesticks, a silver cup, a figure, books, thimbles); two glazed doors, each a frame with glazing bars
    (2 x 4 panes), their panes cut-out glass; a three-step crown. Footprint 0.06-0.94 x 0.47-1 x 0-1.9 as before."""
    w, br = "mahogany", "brass"
    z0 = 7.6
    els = [b("Foot", (0.75, 0, 7.25), (15.25, 1.25, 16), w), b("Skirt", (1, 1.25, z0), (15, 3, 16), w),
           b("SideL", (1, 3, z0), (2, 27, 16), w), b("SideR", (14, 3, z0), (15, 27, 16), w),
           b("Back", (2, 3, 15.5), (14, 27, 16), w, faces=("south", "east", "west")),
           b("Lining", (2, 3, 15.0), (14, 27, 15.5), "l5curioback", faces=("north", "east", "west", "up", "down")),
           b("Floor", (2, 3, 8.0), (14, 4.5, 15.0), w, faces=("up", "north")),
           b("TopRail", (2, 26, z0), (14, 27, 8.4), w, faces=("north", "east", "west", "down", "up"))]
    # the doors: two frames of glazing bars (2 x 4 panes each), meeting at x 8
    for side, (x1, x2) in (("L", (2.0, 8.0)), ("R", (8.0, 14.0))):
        frame, _ = K.frame_members("Door" + side, x1, 4.5, x2, 26, z0, 8.4, 0.9, w, grid=(2, 4), mid=0.5)
        els += frame
        els.append(b("Pane" + side, (x1, 4.5, 8.0), (x2, 26, 8.1), "l5glass", faces=("north",),
                     uv=[0, 0, 6, 16] if side == "L" else [6, 0, 12, 16]))
    els += [b("KnobL", (7.0, 14.5, 6.9), (7.6, 15.5, z0), br), b("KnobR", (8.4, 14.5, 6.9), (9.0, 15.5, z0), br)]
    # glass shelves and what is on them
    for i, y in enumerate((11.0, 17.5, 24.0)):
        els.append(b(f"Shelf{i}", (2, y, 8.6), (14, y + 0.5, 15), "l5shelf", faces=("north", "up", "down", "east", "west")))
    # level 0 (y 4.5): a vase, a pair of plates on edge, a silver cup
    els += [b("VaseFoot", (3.5, 4.5, 10.5), (5.5, 5.0, 12.5), "l5vase"), b("VaseBody", (3.0, 5.0, 10.0), (6.0, 8.5, 13.0), "l5vase"),
            b("VaseNeck", (3.75, 8.5, 10.75), (5.25, 10.0, 12.25), "l5vase"), b("VaseLip", (3.5, 10.0, 10.5), (5.5, 10.5, 12.5), "l5vase"),
            b("Plate0", (7.5, 5.0, 13.0), (11.0, 9.5, 13.5), "l5china"), b("PlateStand0", (8.5, 4.5, 12.5), (10.0, 5.0, 14.0), br),
            b("CupFoot", (11.5, 4.5, 11.0), (13.5, 5.0, 13.0), "l5silver"), b("CupStem", (12.25, 5.0, 11.75), (12.75, 6.5, 12.25), "l5silver"),
            b("CupBowl", (11.5, 6.5, 11.0), (13.5, 9.0, 13.0), "l5silver")]
    # level 1 (y 11.5): a figure on a base, two candlesticks, a stack of books
    els += [b("FigBase", (3.0, 11.5, 10.5), (5.5, 12.0, 13.0), "l5china"), b("FigBody", (3.5, 12.0, 11.0), (5.0, 14.5, 12.5), "l5china"),
            b("FigHead", (3.75, 14.5, 11.25), (4.75, 15.5, 12.25), "l5china"),
            b("CandleA", (7.0, 11.5, 11.0), (8.5, 12.0, 12.5), br), b("StemA", (7.5, 12.0, 11.5), (8.0, 14.5, 12.0), br),
            b("CupA", (7.0, 14.5, 11.0), (8.5, 15.0, 12.5), br),
            b("CandleB", (9.0, 11.5, 11.0), (10.5, 12.0, 12.5), br), b("StemB", (9.5, 12.0, 11.5), (10.0, 14.5, 12.0), br),
            b("CupB", (9.0, 14.5, 11.0), (10.5, 15.0, 12.5), br),
            b("Book0", (11.0, 11.5, 9.5), (13.5, 13.0, 13.5), "l5leather"), b("Book1", (11.25, 13.0, 10.0), (13.25, 14.0, 13.0), "l5leather")]
    # level 2 (y 18): two plates leaning, a teacup and a small brass clock
    els += [b("Plate1", (3.5, 18.5, 13.0), (7.0, 22.5, 13.5), "l5china"), b("PlateStand1", (4.5, 18.0, 12.5), (6.0, 18.5, 14.0), br),
            b("TeaSaucer", (8.5, 18.0, 10.5), (11.0, 18.5, 13.0), "l5china"), b("TeaCup", (9.0, 18.5, 11.0), (10.5, 20.5, 12.5), "l5china"),
            b("ClockBody", (11.5, 18.0, 11.0), (13.5, 21.0, 13.0), br), b("ClockTop", (12.0, 21.0, 11.5), (13.0, 21.5, 12.5), br)]
    # level 3 (y 24.5): thimbles and a cup
    els += [b("Thimble0", (3.5, 24.5, 11.0), (4.7, 25.5, 12.2), "l5silver"), b("Thimble1", (5.5, 24.5, 11.0), (6.7, 25.5, 12.2), "l5silver"),
            b("Miniature", (8.0, 24.5, 12.0), (10.5, 25.5, 13.0), "l5china"), b("Thimble2", (11.5, 24.5, 11.0), (12.7, 25.5, 12.2), br)]
    # the crown: three steps
    els += [b("Cornice", (0.75, 27, 7.2), (15.25, 28, 16), w), b("Cove", (0.5, 28, 6.8), (15.5, 29, 16), w),
            b("Cap", (0.75, 29, 7.2), (15.25, 30, 16), w)]
    return els


# ======================= Ice machine =======================

def ice_machine():
    """A stainless ice machine, front to the north (0.06-0.94 x 0.18-0.94 x 0-1.62): a dark kick under a bevelled
    stainless cabinet and lid, a louvred grille low on the front, the bin door with a gasketed window and a long pull,
    a navy ICE nameplate over it, and a drain pipe down the east side."""
    from gen_shapes import louvre
    s, dk = "l5icesteel", "l5icedark"
    els = [b("Kick", (1.5, 0, 3.5), (14.5, 2.0, 14.5), dk, faces=NOD)]
    els += K.bevelled_box("Body", (1, 2, 3), (15, 25, 15), s, b=0.25)
    els += K.bevelled_box("Lid", (0.75, 25, 2.75), (15.25, 26, 15.25), s, b=0.25)
    els += louvre("Grille", 3, 2.5, 13, 5.5, 3, 4, tex=s, back=dk, frame=0.5, proud=0.5)
    # the bin door, standing out 1 from the face
    els += K.bevelled_box("Door", (2.5, 6.5, 2.0), (13.5, 17.0, 3.0), s, b=0.25)
    ring = K.frame_members("WinRing", 4.0, 8.0, 12.0, 14.5, 1.7, 2.0, 0.5, dk)[0]
    for e in ring:
        e["faces"].pop("south", None)
    els += ring
    els.append(b("WinPane", (4.5, 8.5, 1.85), (11.5, 14.0, 2.0), "l5icewin", faces=("north",), uv=[0, 0, 7, 5.5]))
    els += K.handle("Pull", 8.0, 15.8, 2.0, length=7.0, axis="x", standoff=0.9, thick=0.6, tex=s)
    els.append(b("Label", (2.0, 18.0, 2.5), (14.0, 24.0, 3.0), "l5icelabel", faces=("north",), uv=[0, 0, 12, 6]))
    els.append(b("LabelEdge", (2.0, 18.0, 2.5), (14.0, 24.0, 3.0), s, faces=("east", "west", "up", "down")))
    els += [b("Drain", (15.0, 0, 9.8), (15.9, 4.6, 10.7), "l5icepvc", faces=("north", "east", "south", "up")),
            b("DrainCollar", (14.9, 4.2, 9.7), (16.0, 4.8, 10.8), "l5icepvc")]
    return els


# ======================= Nightstand =======================

def _turned_leg(name, x, z, h=3.0):
    """A turned leg: a foot, a tapering stem, a bead, a shoulder under the apron."""
    return [b(name + "Foot", (x - 0.6, 0, z - 0.6), (x + 0.6, 0.6, z + 0.6), "mahogany"),
            b(name + "Stem", (x - 0.45, 0.6, z - 0.45), (x + 0.45, 1.6, z + 0.45), "mahogany", faces=("north", "east", "south", "west")),
            b(name + "Bead", (x - 0.7, 1.6, z - 0.7), (x + 0.7, 2.2, z + 0.7), "mahogany"),
            b(name + "Neck", (x - 0.55, 2.2, z - 0.55), (x + 0.55, h, z + 0.55), "mahogany", faces=("north", "east", "south", "west"))]


def nightstand():
    """A mahogany nightstand with a moulded top, a drawer with a brass bar pull, an open shelf under it, turned legs, and
    the brass-footed lamp with its glowing shade (the shade is the light: a plain box). Footprint as before (2-14 x 4-14,
    10.4 high; the lamp stands on it)."""
    w = "mahogany"
    els = []
    for i, (x, z) in enumerate(((2.9, 4.9), (13.1, 4.9), (2.9, 13.1), (13.1, 13.1))):
        els += _turned_leg(f"Leg{i}", x, z)
    els += [b("Bottom", (2, 3, 4), (14, 3.5, 14), w, faces=("north", "east", "south", "west", "up")),
            b("SideL", (2, 3.5, 4), (2.75, 9.5, 14), w), b("SideR", (13.25, 3.5, 4), (14, 9.5, 14), w),
            b("Back", (2.75, 3.5, 13.25), (13.25, 9.5, 14), w, faces=("north", "south", "up", "down")),
            b("Core", (2.75, 5.5, 4), (13.25, 9.5, 13.25), w, faces=("north", "down"))]
    els += K.frame_and_panel("Drawer", (2.5, 6.0, 3.2), (13.5, 9.3, 4.0), w, border=0.9, depth=0.25, grid=(1, 1), raised=0.0,
                             both_sides=False)
    els += K.handle("Pull", 8.0, 7.65, 3.2, length=3.0, axis="x", standoff=0.7, thick=0.5, tex="brass")
    els += K.bevelled_box("Top", (1.5, 9.5, 3.5), (14.5, 10.4, 14.5), w, b=0.25)
    # the lamp: an octagonal brass foot, a stem with a bead, a harp-less neck, the shade (the light)
    octagon = _octagon()
    els += octagon("LampFoot", 8, 9, 2.0, 10.4, 11.0, "brass", faces=("north", "east", "south", "west", "up"), lift=0.01)
    els += [b("LampStem", (7.5, 11.0, 8.5), (8.5, 15, 9.5), "brass", faces=("north", "east", "south", "west")),
            b("LampBead", (7.2, 12.4, 8.2), (8.8, 13.2, 9.8), "brass"),
            b("Shade", (5, 14, 6.5), (11, 19, 12.5), "lampshade", glow=90),
            b("Finial", (7.6, 19, 8.6), (8.4, 19.8, 9.4), "brass", faces=NOD)]
    return els


# ======================= Bed =======================

def _bed_common(z1, z2):
    """The sleeping part of a bed half from z1 to z2 (its frame rails, skirt, mattress): returns elements."""
    els = [b("RailL", (1, 4.5, z1), (2, 6, z2), "mahogany", faces=("north", "west", "up", "south")),
           b("RailR", (14, 4.5, z1), (15, 6, z2), "mahogany", faces=("north", "east", "up", "south")),
           b("Skirt", (1.2, 1.5, z1), (14.8, 4.5, z2), "l5skirt", faces=("north", "east", "south", "west"))]
    return els


def bed_head():
    """The head half of a hotel bed (front to the north; the headboard at the north end): a tall mahogany headboard, two
    posts with finials, a crest and a recessed and fielded panel; a burgundy bed skirt under mahogany rails; a ticking
    mattress, two pillows, the sheet turned down over a quilted coverlet. Footprint as before (full block, 0.6 high)."""
    w = "mahogany"
    els = []
    for side, x in (("L", 0.5), ("R", 14.0)):
        els += K.bevelled_box("Post" + side, (x, 0, -0.5), (x + 1.5, 16, 1.0), w, b=0.25)
        els.append(b("Finial" + side, (x + 0.25, 16, -0.25), (x + 1.25, 17.25, 0.75), w, faces=NOD))
    els += K.frame_and_panel("Head", (2, 3.5, -0.5), (14, 12.5, 1.0), w, border=1.25, depth=0.4, grid=(2, 1), raised=0.25)
    els += K.bevelled_box("Crest", (2, 12.5, -0.75), (14, 15.0, 1.25), w, b=0.25)
    els += _bed_common(1.0, 16)
    mat = {"top": "l5sheet", "side": "l5mattress", "front": "l5mattress", "back": "l5mattress", "bottom": "l5mattress"}
    els += K.bevelled_box("Mattress", (1.25, 6, 1.0), (14.75, 9.0, 16), mat, b=0.25)
    # the coverlet, from z 6.5 on, hanging over the mattress's sides; the sheet turned back over it
    els.append(b("Coverlet", (0.9, 6.6, 6.5), (15.1, 9.6, 16), {"top": "l5coverlet", "side": "l5coverlet", "front": "l5coverlet",
                                                                  "back": "l5coverlet", "bottom": "l5coverlet"}, faces=("north", "east", "west", "up")))
    els.append(b("Fold", (1.0, 9.0, 5.0), (15.0, 9.7, 6.5), "l5sheet", faces=("north", "east", "west", "up", "south")))
    els += K.bevelled_box("PillowL", (2.0, 9.0, 1.75), (7.5, 11.5, 5.0), "l5pillow", b=0.5)
    els += K.bevelled_box("PillowR", (8.5, 9.0, 1.75), (14.0, 11.5, 5.0), "l5pillow", b=0.5)
    return els


def bed_foot():
    """The foot half: the mattress and quilted coverlet running to the foot, the coverlet hanging over its end, the
    skirt, rails and a low footboard (two posts with finials round a recessed and fielded panel). Footprint as before."""
    w = "mahogany"
    els = []
    for side, x in (("L", 0.5), ("R", 14.0)):
        els += K.bevelled_box("Post" + side, (x, 0, 14.5), (x + 1.5, 12, 16), w, b=0.25)
        els.append(b("Finial" + side, (x + 0.25, 12, 14.75), (x + 1.25, 13.25, 15.75), w, faces=NOD))
    els += K.frame_and_panel("Foot", (2, 3.0, 14.75), (14, 10.5, 15.75), w, border=1.25, depth=0.25, grid=(2, 1), raised=0.0)
    els += _bed_common(0, 14.5)
    mat = {"top": "l5sheet", "side": "l5mattress", "front": "l5mattress", "back": "l5mattress", "bottom": "l5mattress"}
    els += K.bevelled_box("Mattress", (1.25, 6, 0), (14.75, 9.0, 14.0), mat, b=0.25)
    cov = {"top": "l5coverlet", "side": "l5coverlet", "front": "l5coverlet", "back": "l5coverlet", "bottom": "l5coverlet"}
    els.append(b("Coverlet", (0.9, 6.6, 0), (15.1, 9.6, 14.4), cov, faces=("south", "east", "west", "up")))
    return els


# ======================= Grandfather clock =======================

def grandfather_clock():
    """A mahogany longcase clock (footprint 0.18-0.82 x 0.36-0.88, 1.95 high): a stepped plinth with a raised base panel,
    a trunk with quarter-columns and a glazed door showing a brass pendulum and two weights on chains, a hood with a
    moulded cornice, a round dial (octagonal brass bezel, crisp ivory face with numerals, cut-out glass) with the hands
    as geometry (10:10), a pediment and a brass finial."""
    w, br = "mahogany", "brass"
    els = [b("PlinthFoot", (3, 0, 6), (13, 1.5, 14), w), b("PlinthBody", (3.5, 1.5, 6.25), (12.5, 5.0, 13.75), w),
           b("PlinthCap", (3, 5.0, 6), (13, 6.5, 14), w), b("Base", (3.25, 6.5, 6.25), (12.75, 10.5, 13.75), w),
           b("BaseField", (4.5, 7.25, 5.75), (11.5, 10.0, 6.25), w, faces=NOS),
           b("BaseBead", (4.0, 6.75, 5.95), (12.0, 7.25, 6.25), w, faces=NOS)]
    # the trunk is hollow behind its door: no front face on the body, the frame and strips close the front
    els += [b("Trunk", (4, 10.5, 7.6), (12, 24, 13.5), w, faces=("east", "west", "south", "up", "down")),
            b("ColL", (4.0, 10.5, 6.1), (4.6, 24, 7.6), w, faces=NOS), b("ColR", (11.4, 10.5, 6.1), (12.0, 24, 7.6), w, faces=NOS),
            b("DoorTop", (4.6, 23.0, 6.1), (11.4, 24.0, 7.6), w, faces=NOS), b("DoorBottom", (4.6, 10.5, 6.1), (11.4, 11.0, 7.6), w, faces=NOS)]
    # the trunk door: a frame round the glazed opening (5.7-10.3 x 12.1-21.9)
    frame, _ = K.frame_members("TrunkDoor", 4.6, 11.0, 11.4, 23.0, 6.0, 7.6, 1.1, w)
    els += frame
    els.append(b("Inner", (5.7, 12.1, 9.0), (10.3, 21.9, 9.1), "l5clockinner", faces=("north",), uv=[0, 0, 4.6, 9.8]))
    els.append(b("Rod", (7.75, 14.5, 7.4), (8.25, 21.0, 7.9), br, faces=("north", "east", "west")))
    els += [b("BobA", (6.9, 12.7, 7.2), (9.1, 14.9, 8.0), br, faces=("north", "east", "west", "up", "down")),
            b("BobB", (6.9, 12.7, 7.0), (9.1, 14.9, 7.8), br, faces=("north", "east", "west", "up", "down"), rot=(0, 0, 45))]
    els += [b("WeightL", (6.0, 16.0, 7.2), (7.4, 19.5, 8.6), br), b("ChainL", (6.45, 19.5, 7.8), (6.95, 21.9, 8.3), "l5hand"),
            b("WeightR", (8.6, 13.5, 7.6), (10.0, 17.0, 9.0), br)]
    els.append(b("TrunkGlass", (5.7, 12.1, 6.2), (10.3, 21.9, 6.3), "l5glass", faces=("north",), uv=[0, 0, 4.6, 16]))
    # the hood
    els += [b("HoodBase", (2.75, 24, 5.75), (13.25, 24.75, 14.25), w),
            b("Hood", (3, 24.75, 6.25), (13, 32, 14), w),
            b("PilasterL", (3.0, 25.0, 5.9), (3.9, 31.5, 6.25), w, faces=NOS), b("PilasterR", (12.1, 25.0, 5.9), (13.0, 31.5, 6.25), w, faces=NOS),
            b("Cornice", (2.75, 32, 5.75), (13.25, 32.75, 14.25), w), b("CorniceCap", (3.25, 32.75, 6.25), (12.75, 33.25, 13.75), w),
            b("Pediment", (5.5, 33.25, 7.5), (10.5, 34.0, 12.5), w), b("Plinth", (7.0, 34.0, 8.5), (9.0, 34.6, 10.5), br),
            b("Finial", (7.5, 34.6, 9.0), (8.5, 36.0, 10.0), br)]
    cx, cy, zf = 8.0, 28.4, 6.25
    dial = K.dial("Dial", cx, cy, zf, r=3.4, face="l5clockface", bezel=br, needle="l5hand", glass="l5clockglass")
    dial = [e for e in dial if not e["name"].endswith(("Needle", "Hub"))]
    els += dial
    # the hands, 10:10: the hour hand pointing at 10 (300 degrees), the minute hand at 2 (60), thin and pointed enough
    for nm, ln, ang, zz, wd in (("HourHand", 1.9, 305.0, (-0.5, -0.35), 0.5), ("MinuteHand", 2.7, 60.0, (-0.35, -0.2), 0.5)):
        els.append(b(nm, (cx - wd / 2, cy - 0.5, zf + zz[0] - 0.1), (cx + wd / 2, cy + ln, zf + zz[1] - 0.1), "l5hand",
                     faces=("north", "east", "west", "up"), rot=(0, 0, -ang), origin=(cx, cy, zf)))
    els.append(b("HandHub", (cx - 0.5, cy - 0.5, zf - 0.75), (cx + 0.5, cy + 0.5, zf - 0.5), br, faces=NOS))
    return els


# ======================= Gilt mirror =======================

def gilt_mirror():
    """The hotel's gilt mirror, on a wall block's north face (z < 0 out of it), a plain wall behind: a gilt frame
    (outer ring 1 wide) with a bead along its middle and a bevelled glass edge (a slim polished ring) round a larger
    pane (11.5 x 12.5 visible, was 8.4 x 14.4 in an old 0.8 frame) with a soft band of light and a bright line."""
    g = "gilt"

    def ring(name, x1, y1, x2, y2, w, z1, z2, tex, faces=("north", "east", "west", "up", "down")):
        return [b(name + "T", (x1, y2 - w, z1), (x2, y2, z2), tex, faces=faces),
                b(name + "B", (x1, y1, z1), (x2, y1 + w, z2), tex, faces=faces),
                b(name + "L", (x1, y1 + w, z1), (x1 + w, y2 - w, z2), tex, faces=("north", "east", "west")),
                b(name + "R", (x2 - w, y1 + w, z1), (x2, y2 - w, z2), tex, faces=("north", "east", "west"))]
    els = ring("Frame", 0.75, 0.25, 15.25, 15.75, 1.0, -1.0, 0, g)
    els += ring("Bead", 1.0, 0.5, 15.0, 15.5, 0.5, -1.35, -1.0, g)
    els.append(b("Glass", (1.75, 1.25, -0.45), (14.25, 14.75, -0.35), "l5mirror", faces=("north",), uv=[0, 0, 16, 16]))
    els += ring("Bevel", 1.75, 1.25, 14.25, 14.75, 0.5, -0.6, -0.35, "l5mirrorbevel", faces=("north",))
    return els


# ======================= Turntable =======================

def turntable():
    """A 1920s phonograph console in mahogany (footprint 2-14 x 2-14, the old block's; 10.4 high to the record): bun
    feet under a moulded plinth, a bevelled cabinet with a brass-framed gold speaker cloth on the front and a brass
    crank on the east side, a moulded top with a green baize deck, and on it a steel platter carrying a shellac record
    (a round label, a spindle), a tonearm on a brass pivot with a counterweight and a headshell with its needle resting
    on the grooves, and a volume knob. The lid is propped open at the back, lined with velvet."""
    octagon = _octagon()
    w, br = "mahogany", "brass"
    els = []
    for i, (x, z) in enumerate(((2.5, 2.5), (11.5, 2.5), (2.5, 11.5), (11.5, 11.5))):
        els += [b(f"Foot{i}", (x, 0, z), (x + 2, 0.7, z + 2), w, faces=NOD),
                b(f"Ankle{i}", (x + 0.25, 0.7, z + 0.25), (x + 1.75, 1.4, z + 1.75), w, faces=("north", "east", "south", "west"))]
    els.append(b("Plinth", (2, 1.4, 2), (14, 2.2, 14), w))
    els += K.bevelled_box("Body", (2.5, 2.2, 2.5), (13.5, 8.5, 13.5), w, b=0.25)
    # the speaker: a gold cloth behind a brass frame
    els += K.frame_members("Grille", 4, 3.2, 12, 7.6, 1.9, 2.5, 0.5, br)[0]
    els.append(b("Cloth", (4.5, 3.7, 2.0), (11.5, 7.1, 2.5), "l5ttcloth", faces=("north",)))
    # the crank on the east side
    els += [b("CrankStub", (13.5, 5.4, 7.5), (14.5, 5.9, 8.0), br, faces=("north", "east", "south", "up", "down")),
            b("CrankArm", (14.5, 3.9, 7.5), (15.0, 5.9, 8.0), br),
            b("CrankKnob", (14.3, 3.4, 7.25), (15.2, 3.9, 8.25), w)]
    els += K.bevelled_box("Top", (1.75, 8.5, 1.75), (14.25, 9.5, 14.25), w, b=0.25)
    els.append(b("Baize", (2.75, 9.5, 2.75), (13.75, 9.75, 13.25), "felt", faces=("north", "east", "south", "west", "up")))
    # the platter and the record
    cx, cz = 7.6, 8.2
    els += octagon("Platter", cx, cz, 4.9, 9.75, 10.05, "l5platter", faces=("north", "east", "south", "west", "up"), lift=0.005)
    els += octagon("RecordEdge", cx, cz, 4.6, 10.05, 10.5, "l5vinylside", faces=("north", "east", "south", "west"))
    els.append(b("Record", (cx - 4.75, 10.5, cz - 4.75), (cx + 4.75, 10.55, cz + 4.75), "l5record", faces=("up",), uv=[0, 0, 9.5, 9.5]))
    els.append(b("Spindle", (cx - 0.25, 10.55, cz - 0.25), (cx + 0.25, 11.3, cz + 0.25), br, faces=("north", "east", "south", "west", "up")))
    # the tonearm: pivot base, collar, a tube turned toward the record, the counterweight behind and the headshell
    px, pz = 12.9, 4.2
    els += [b("ArmBase", (px - 0.8, 9.75, pz - 0.8), (px + 0.8, 10.4, pz + 0.8), br, faces=NOD),
            b("ArmCollar", (px - 0.5, 10.4, pz - 0.5), (px + 0.5, 11.2, pz + 0.5), br, faces=NOD)]
    th = math.degrees(math.atan2(-2.55, 2.25))
    els += [b("Arm", (px - 0.25, 11.2, pz), (px + 0.25, 11.7, pz + 3.4), br, rot=(0, th, 0), origin=(px, 11.2, pz)),
            b("Counterweight", (px - 0.5, 11.0, pz - 1.4), (px + 0.5, 12.0, pz - 0.2), br, rot=(0, th, 0), origin=(px, 11.2, pz))]
    ex, ez = px + 3.4 * math.sin(math.radians(th)), pz + 3.4 * math.cos(math.radians(th))
    els += [b("Headshell", (ex - 0.5, 10.9, ez), (ex + 0.5, 11.4, ez + 1.3), br, rot=(0, -75, 0), origin=(ex, 11.2, ez)),
            b("Needle", (ex - 0.25, 10.55, ez + 1.0), (ex + 0.25, 10.9, ez + 1.3), "l5platter", rot=(0, -75, 0), origin=(ex, 11.2, ez))]
    els += K.bevelled_box("Knob", (3.1, 9.75, 2.9), (4.1, 10.5, 3.9), br, b=0.25)
    # the lid, hinged at the back (z 13.5, y 9.5) and propped open: its outside faces the back, its velvet lining the front
    hinge = (8.0, 9.5, 13.5)
    els += [b("LidShell", (2.25, 9.75, 2.5), (13.75, 10.25, 13.5), w, rot=(97, 0, 0), origin=hinge),
            b("LidLining", (2.75, 9.5, 3.0), (13.25, 9.75, 13.0), "l5curioback", faces=("down",), rot=(97, 0, 0), origin=hinge)]
    return els


# ======================= Room service tray =======================

def room_service_tray():
    """A silver-plated room service tray (3.2-12.8 x 3.9-12.1 x up to 1.6, front to the north), its plate worn to copper
    at the corners: a floor, walls with a rolled lip and a tab handle at each short end, a starched cloth, and on it a
    domed cloche on a china plate (brass knob), a cup of coffee on a saucer with a teaspoon, a folded napkin with a
    knife on it, a fork, and a bud vase with a red rose."""
    octagon = _octagon()
    t = "l5trayplate"
    side = ("north", "east", "south", "west", "up")
    els = [b("Floor", (3.2, 0, 3.9), (12.8, 0.4, 12.1), t),
           b("WallN", (3.2, 0.4, 3.9), (12.8, 1.3, 4.4), t, faces=("north", "east", "south", "west")),
           b("WallS", (3.2, 0.4, 11.6), (12.8, 1.3, 12.1), t, faces=("north", "east", "south", "west")),
           b("WallW", (3.2, 0.4, 4.4), (3.7, 1.3, 11.6), t, faces=("north", "south", "west", "up")),
           b("WallE", (12.3, 0.4, 4.4), (12.8, 1.3, 11.6), t, faces=("north", "south", "east", "up")),
           b("LipN", (3.2, 1.3, 3.9), (12.8, 1.6, 4.6), t, faces=("north", "east", "south", "west", "up")),
           b("LipS", (3.2, 1.3, 11.4), (12.8, 1.6, 12.1), t, faces=("north", "east", "south", "west", "up")),
           b("LipW", (3.2, 1.3, 4.6), (3.9, 1.6, 11.4), t, faces=("north", "south", "west", "up")),
           b("LipE", (12.1, 1.3, 4.6), (12.8, 1.6, 11.4), t, faces=("north", "south", "east", "up"))]
    # a tab handle at each end
    els += [b("HandleW", (2.7, 0.6, 6.3), (3.2, 1.1, 9.7), t, faces=("north", "south", "west", "up", "down")),
            b("HandleWTip", (2.4, 0.6, 6.8), (2.7, 1.1, 9.2), t, faces=("north", "south", "west", "up", "down")),
            b("HandleE", (12.8, 0.6, 6.3), (13.3, 1.1, 9.7), t, faces=("north", "south", "east", "up", "down")),
            b("HandleETip", (13.3, 0.6, 6.8), (13.6, 1.1, 9.2), t, faces=("north", "south", "east", "up", "down"))]
    els.append(b("Cloth", (3.9, 0.4, 4.6), (12.1, 0.9, 11.4), "l5sheet", faces=side))
    # the cloche on its plate
    cx, cz = 6.5, 8.2
    els += octagon("CPlate", cx, cz, 2.6, 0.9, 1.1, "l5china", faces=side, lift=0.005)
    ys = (1.1, 1.45, 1.8, 2.15, 2.5, 2.8, 3.05, 3.25, 3.4)  # a domed profile, an ellipse 2.4 wide and 2.4 high, as steps
    for k in range(len(ys) - 1):
        mid = ((ys[k] + ys[k + 1]) / 2 - 1.1) / 2.4
        els += octagon(f"Dome{k}", cx, cz, round(2.4 * math.sqrt(max(0.0, 1 - mid * mid)), 2), ys[k], ys[k + 1], "l5silver", faces=side, lift=0.005)
    els += octagon("CKnob", cx, cz, 0.55, 3.4, 4.1, "brass", faces=("north", "east", "south", "west", "up"), lift=0.005)
    # coffee: saucer, cup, handle, the coffee, a teaspoon
    kx, kz = 10.7, 9.3
    els += octagon("Saucer", kx, kz, 1.35, 0.9, 1.1, "l5china", faces=side, lift=0.005)
    els += octagon("Cup", kx, kz, 0.85, 1.1, 1.9, "china", faces=("north", "east", "south", "west", "up"), lift=0.005)
    els += octagon("Coffee", kx, kz, 0.65, 1.9, 1.95, "l5coffee", faces=("up",), lift=0.003)
    els += [b("CupHandle", (kx + 0.85, 1.2, kz - 0.25), (kx + 1.3, 1.7, kz + 0.25), "china"),
            b("SpoonBowl", (9.9, 1.1, 7.95), (10.6, 1.3, 8.4), "l5silver", faces=side),
            b("SpoonHandle", (10.6, 1.1, 8.05), (11.9, 1.3, 8.3), "l5silver", faces=side)]
    # the napkin, folded, with a knife across it; a fork on the cloth
    els += [b("Napkin", (9.0, 0.9, 4.8), (10.5, 1.25, 6.2), "l5napkin", faces=side),
            b("NapkinFold", (9.0, 1.25, 4.8), (10.5, 1.5, 5.4), "l5napkin", faces=side),
            b("KnifeBlade", (9.1, 1.25, 5.6), (10.0, 1.45, 6.1), "l5silver", faces=side),
            b("KnifeHandle", (10.0, 1.25, 5.65), (10.45, 1.5, 6.05), "china", faces=side)]
    els += [b("ForkTine1", (3.9, 0.9, 4.7), (4.9, 1.15, 5.1), "l5silver", faces=side),
            b("ForkTine2", (3.9, 0.9, 5.3), (4.9, 1.15, 5.7), "l5silver", faces=side),
            b("ForkHead", (4.9, 0.9, 4.7), (5.3, 1.15, 5.7), "l5silver", faces=side),
            b("ForkHandle", (5.3, 0.9, 5.0), (8.2, 1.15, 5.4), "l5silver", faces=side)]
    # the bud vase and its rose
    vx, vz = 11.4, 5.6
    els += octagon("VaseBase", vx, vz, 0.6, 0.9, 1.4, "l5vase", faces=side, lift=0.005)
    els += octagon("VaseBody", vx, vz, 0.5, 1.4, 2.8, "l5vase", faces=("north", "east", "south", "west"), lift=0.005)
    els += octagon("VaseLip", vx, vz, 0.65, 2.8, 3.2, "l5vase", faces=side, lift=0.005)
    els += [b("Stem", (vx - 0.25, 3.2, vz - 0.25), (vx + 0.25, 4.8, vz + 0.25), "l5stem", faces=("north", "east", "south", "west")),
            b("Leaf", (vx + 0.25, 3.7, vz - 0.25), (vx + 1.0, 3.95, vz + 0.25), "l5stem", rot=(0, 0, 25), origin=(vx + 0.25, 3.8, vz)),
            b("Bloom", (vx - 0.6, 4.8, vz - 0.6), (vx + 0.6, 5.7, vz + 0.6), "l5rose"),
            b("BloomTop", (vx - 0.4, 5.7, vz - 0.4), (vx + 0.4, 6.0, vz + 0.4), "l5rose", faces=side)]
    return els
