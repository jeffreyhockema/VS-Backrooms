"""The Hub's doors (for tools/gen_hub.py): the carved concrete level doors, their sigils and carved sides, the pink
ribbon door to Level 974, the grey service doors and the Tower's ornate doors. All are set into a wall with their face
to the north; "l" is the viewer's left (+X in the -north variant).
"""
import math

import gen_hub_sigils as SIG
from gen_hub_kit import (DIRS, FRONT, METAL, ROTATE, SIDES, STONE, WOOD, block, bx, mirror_x, name, relief, shape)

N = 32  # relief cells across a face (half a unit each)


def depth_grid(fn):
    """A 32 x 32 height map from fn(u, v): u from the viewer's left, v from the top, in units (cell centres)."""
    return [[fn((c + 0.5) * 16 / N, (r + 0.5) * 16 / N) for c in range(N)] for r in range(N)]


def in_wall(extra=None, kind=None, sounds=STONE, resistance=20, behavior=None):
    """Block-type fields for a block set into a wall: solid, opaque to light, fixed in place."""
    data = {"sidesolid": {"all": True}, "sideopaque": {"all": False}, "lightAbsorption": 99, "resistance": resistance,
            "drops": [], "sounds": sounds}
    if kind:
        data["behaviors"] = [{"name": "BackroomsThreshold", "properties": {"kind": kind}}]
    if behavior:
        data["behaviors"] = [{"name": behavior}]
    if extra:
        data.update(extra)
    return data


def oriented_parts(code, groups, shapes, first, material, fields, comment, english):
    data = {"variantgroups": [{"code": g, "states": s} for g, s in groups] + [{"code": "side", "states": SIDES}],
            "creativeinventory": {"general": [first], "decorative": [first]},
            "blockmaterial": material, "drawtype": "json",
            "shapeByType": {f"*-{k}-{s}": {"base": p, "rotateY": ROTATE[s]} for k, p in shapes.items() for s in SIDES}}
    data.update(fields)
    block(code, data, comment)
    name(code + "-*", english)


class Face:
    """Collects boxes given in viewer coordinates of a north face (u from the left, v from the top) and depth z."""

    def __init__(self):
        self.els = []

    def box(self, nm, ua, ub, va, vb, z1, z2, t, faces=FRONT, glow=0):
        self.els.append(bx(nm, (16 - ub, 16 - vb, z1), (16 - ua, 16 - va, z2), t, faces=faces, glow=glow))


FRAME, BAND, GAP = 3.0, 1.5, 0.5  # carved door: frame width on the outer edges, the border round the slab, the gap
LEAF, RIM, GAPZ = 2.5, 2.0, 4.5     # depths behind the wall plane: the slab's face, its border band, the gap's floor


def door_part(col, row, leaf="doorleaf", low="doorleaf-low", frame="doorframe", sill="doorsill", extra=None, rails=True):
    """One block of a 3 x 4 carved door. Rows count from the bottom: row 1 carries a half-block sill that meets the
    sidewalk, row 4 the lintel. The frame stands a unit proud of the wall; a dark gap runs round the slab."""
    f = Face()
    tex = low if row == 1 else leaf
    u0 = FRAME if col == "l" else 0
    u1 = 16 - FRAME if col == "r" else 16
    v0 = FRAME if row == 4 else 0
    v1 = 8 if row == 1 else 16
    g = GAP
    # The slab, the shadow gap round it (on the outer sides, under the lintel, over the sill)
    lu0, lu1 = u0 + (g if col == "l" else 0), u1 - (g if col == "r" else 0)
    lv0, lv1 = v0 + (g if row == 4 else 0), v1 - (g if row == 1 else 0)
    f.box("Leaf", lu0, lu1, lv0, lv1, LEAF, 16, tex, faces=DIRS)
    if col == "l":
        f.box("GapL", u0, lu0, v0, v1, GAPZ, 16, "carved-deep")
    if col == "r":
        f.box("GapR", lu1, u1, v0, v1, GAPZ, 16, "carved-deep")
    if row == 4:
        f.box("GapTop", u0, u1, v0, lv0, GAPZ, 16, "carved-deep")
    if row == 1:
        f.box("GapLow", u0, u1, lv1, v1, GAPZ, 16, "carved-deep")
    # Frame: posts on the outer edges and the lintel, proud of the wall, with a chamfered inner step
    if col == "l":
        f.box("Post", 0, FRAME - 1, 0, 16, -1, 16, frame)
        f.box("PostStep", FRAME - 1, FRAME, 0 if row != 4 else FRAME - 1, 16, -0.4, 16, frame)
    if col == "r":
        f.box("Post", 16 - FRAME + 1, 16, 0, 16, -1, 16, frame)
        f.box("PostStep", 16 - FRAME, 16 - FRAME + 1, 0 if row != 4 else FRAME - 1, 16, -0.4, 16, frame)
    if row == 4:
        f.box("Lintel", FRAME - 1 if col == "l" else 0, 16 - FRAME + 1 if col == "r" else 16, 0, FRAME - 1, -1, 16, frame)
        f.box("LintelStep", FRAME if col == "l" else 0, 16 - FRAME if col == "r" else 16, FRAME - 1, FRAME, -0.4, 16, frame)
    if row == 1:
        # (its ends a hair inside the posts' outer faces, not in their plane)
        f.box("Sill", 0.05 if col == "l" else 0, 15.95 if col == "r" else 16, 8, 16, -1.2, 16, sill, faces=DIRS)
    # The raised border round the whole slab: along the outer sides, under the lintel, over the sill
    if col == "l":
        f.box("BandL", lu0, lu0 + BAND, lv0, lv1, RIM, LEAF, tex)
    if col == "r":
        f.box("BandR", lu1 - BAND, lu1, lv0, lv1, RIM, LEAF, tex)
    if row == 4:
        f.box("BandTop", lu0, lu1, lv0, lv0 + BAND, RIM, LEAF, tex)
    if row == 1:
        f.box("BandLow", lu0, lu1, lv1 - BAND, lv1, RIM, LEAF, tex)
    # A rail across the middle, where the slab was cast in two lifts
    if rails and row == 2:
        f.box("RailLow", lu0, lu1, 15, 16, RIM, LEAF, tex)
    if rails and row == 3:
        f.box("RailHigh", lu0, lu1, 0, 1, RIM, LEAF, tex)
    if extra:
        extra(f, col, row, u0, u1, v0, v1)
    return f.els


def escutcheon(f):
    """The brass escutcheon on c-2: a plate round a keyhole, six rivets."""
    z1, z2 = 1.7, LEAF
    f.box("PlateL", 6.4, 7.5, 4.5, 12, z1, z2, "brass")
    f.box("PlateR", 8.5, 9.6, 4.5, 12, z1, z2, "brass")
    f.box("PlateT", 7.5, 8.5, 4.5, 6.6, z1, z2, "brass")
    f.box("PlateB", 7.5, 8.5, 9.6, 12, z1, z2, "brass")
    f.box("KeyholeRound", 7.5, 8.5, 6.6, 7.6, z1 + 0.25, z2, "brass")
    f.box("KeyholeL", 7.5, 7.75, 7.6, 9.6, z1 + 0.25, z2, "brass")
    f.box("KeyholeR", 8.25, 8.5, 7.6, 9.6, z1 + 0.25, z2, "brass")
    f.box("KeyholeDark", 7.5, 8.5, 6.6, 9.6, z2 - 0.05, z2 + 0.3, "keyhole", faces=("north",))
    for i, (u, v) in enumerate(((6.95, 5.0), (9.05, 5.0), (6.95, 8.25), (9.05, 8.25), (6.95, 11.5), (9.05, 11.5))):
        f.box(f"Rivet{i}", u - 0.3, u + 0.3, v - 0.3, v + 0.3, z1 - 0.3, z1, "brass")


def carved_extra(f, col, row, u0, u1, v0, v1):
    if col == "c" and row == 2:
        escutcheon(f)


def pink_extra(f, col, row, u0, u1, v0, v1):
    """The pink door's raised panels, its ribbon (round the door both ways, over frame and sill as round a present),
    the bow over the middle and a gold knob."""
    pu0, pu1 = u0 + (1.5 if col == "l" else 2), u1 - (1.5 if col == "r" else 2)
    # Two tall raised panels to each leaf column: rows 1-2 and rows 3-4
    span = {1: (0, 5), 2: (0, 14.5), 3: (1.5, 16), 4: (0, 11.5)}[row]
    # (a hair behind the border bands it meets, so their faces are not in one plane)
    f.box("Panel", pu0, pu1, span[0], span[1], RIM + 0.05, LEAF, "pinkpanel")
    rz1, rz2 = 1.2, RIM
    # The ribbon stands a hair proud of the frame and sill where it runs over them (H = a hair)
    H = 0.05
    if col == "c":
        f.box("RibbonV", 6, 10, v0, 8 if row == 1 else 16, rz1, rz2, "ribbon")
        if row == 4:
            f.box("RibbonLintel", 6, 10, 0, FRAME, -1.5, -1, "ribbon")
            f.box("RibbonLintelTop", 6, 10, -0.01, 0.5, -1.5, -1, "ribbon")
            f.box("RibbonDown", 6, 10, FRAME - 0.5, FRAME + H, -1, rz2, "ribbon")
        if row == 1:
            f.box("RibbonSill", 6, 10, 8.5, 16, -1.7, -1.2, "ribbon")
            f.box("RibbonSillTop", 6, 10, 8 - H, 8.5, -1.7, rz2, "ribbon")
    if row == 3:
        a, b = 0, 16
        if col == "l":
            f.box("RibbonFrame", 0, FRAME, 5, 9, -1.5, -1, "ribbon")
            f.box("RibbonStep", FRAME - 0.5, FRAME + H, 5, 9, -1, rz2, "ribbon")
            a = FRAME
        if col == "r":
            f.box("RibbonFrame", 16 - FRAME, 16, 5, 9, -1.5, -1, "ribbon")
            f.box("RibbonStep", 16 - FRAME - H, 16 - FRAME + 0.5, 5, 9, -1, rz2, "ribbon")
            b = 16 - FRAME
        f.box("RibbonH", a, b, 5, 9, rz1 - (0.2 if col == "c" else 0), rz2, "ribbon")
    if col == "c" and row == 3:
        # The bow: a knot, two loops flaring up and out, two tails falling into the block below
        f.els.append(bx("Knot", (6.4, 6.2, -1.2), (9.6, 9.8, 1.2), "ribbon"))
        for side, sgn in (("L", 1), ("R", -1)):
            cx = 8 + sgn * 5.0
            f.els.append(bx("Loop" + side, (cx - 4.2, 6.0, -1.8), (cx + 4.2, 11.2, 0.9), "ribbon", rot=(0, 0, sgn * 12), origin=(8, 8, 0)))
            f.els.append(bx("LoopIn" + side, (cx - 3.0, 7.2, -1.9), (cx + 2.6, 10.0, -1.8), "pinkpanel", faces=("north",),
                            rot=(0, 0, sgn * 12), origin=(8, 8, 0)))
            tx = 8 + sgn * 1.8
            f.els.append(bx("Tail" + side, (tx - 1.3, -6, -0.5), (tx + 1.3, 7, 0.8), "ribbon", rot=(0, 0, sgn * 16), origin=(tx, 7, 0)))
    if col == "r" and row == 2:
        # A round gold knob, on the right as on any door
        for e in (bx("KnobRose", (2.4, 6.4, 1.6), (5.6, 9.6, RIM), "gold"),
                  bx("KnobStem", (3.4, 7.4, 0.4), (4.6, 8.6, 1.6), "gold"),
                  bx("Knob", (2.3, 6.3, -1.2), (5.7, 9.7, 0.4), "gold"),
                  bx("KnobB", (2.8, 5.8, -1.0), (5.2, 10.2, 0.2), "gold"),
                  bx("KnobC", (1.8, 6.8, -1.0), (6.2, 9.2, 0.2), "gold")):
            f.els.append(e)


def carved_doors():
    groups = [("col", ["l", "c", "r"]), ("row", ["1", "2", "3", "4"])]
    shapes = {f"{c}-{r}": shape(f"door-{c}-{r}", door_part(c, r, extra=carved_extra)) for c in "lcr" for r in (1, 2, 3, 4)}
    oriented_parts("hub-door", groups, shapes, "*-c-2-north", "Stone", in_wall(behavior="BackroomsHubDoor"),
                   "A great carved concrete door of the Hub, 3 wide (col l, c, r: the viewer's left to right) and 4 high"
                   " (row 1-4 from the bottom; row 1 has a half-block sill meeting the sidewalk), set into the wall with its"
                   " face to the north. Behaviour BackroomsHubDoor (HubSystem). c-2 carries the brass keyhole. Its sigil goes above c-4 (hub-sigil), the carved sides"
                   " above l-4 and r-4 (hub-sigilside)", "Concrete Door")
    shapes = {f"{c}-{r}": shape(f"pinkdoor-{c}-{r}", door_part(c, r, leaf="pinkpaint", low="pinkpaint", frame="whitepaint",
                                                                sill="whitepaint", extra=pink_extra, rails=False))
              for c in "lcr" for r in (1, 2, 3, 4)}
    oriented_parts("hub-pinkdoor", groups, shapes, "*-c-3-north", "Wood", in_wall(behavior="BackroomsHubDoor", sounds=WOOD),
                   "The pink door, tied with a ribbon like a present: the same size and parts as hub-door (3 x 4, row 1 with"
                   " a sill), the bow on c-3, a gold knob on r-2. It needs no key: it lets in only someone carrying something"
                   " cute (Level 974). Behaviour BackroomsHubDoor, like the carved doors (HubSystem tells them apart by place)",
                   "Pink Door")


def sigil_depths(n):
    """The sigil over a door: a disc cut 3 deep into the face with a stepped edge, the sigil standing 2.5 proud of
    the floor (in the floor's shadow, so it reads from across the road under the orange haze); the border grooves of
    the carved sides run on into the disc's rim."""
    grid = SIG.raster(n, 28)

    def fn(u, v):
        r = math.hypot(u - 8, v - 8)
        if r > 7:
            return 1.0 if (1 <= v < 2 or 14 <= v < 15) else 0.0
        if r > 6.5:
            return 1.5
        c, row = int((u - 1) * 2), int((v - 1) * 2)
        if 0 <= c < 28 and 0 <= row < 28 and grid[row][c] and r < 6.3:
            return 0.5
        return 3.0
    return depth_grid(fn)


def sigilside_depths():
    """A carved side panel (the viewer's left one; the right is its mirror): a groove round its outer edges, and a
    straight groove leading in to the sigil's ring."""
    def fn(u, v):
        if (1 <= u < 2 and 1 <= v < 15) or (1 <= v < 2 and u >= 1) or (14 <= v < 15 and u >= 1):
            return 1.0
        if 7.5 <= v < 8.5 and u >= 3:
            return 1.0  # a straight path leading in to the sigil's ring, as crop circles are joined
        return 0.0
    return depth_grid(fn)


def carve_tex(d):
    return {0.0: "carved", 0.5: "carved-relief", 0.75: "carved-deep", 1.0: "carved-deep", 1.5: "carved-deep", 3.0: "carved-recess"}[d]


def sigils():
    shapes = {str(n): shape(f"sigil-{n}", relief(sigil_depths(n), carve_tex, back_tex="carved")) for n in SIG.IDS}
    oriented_parts("hub-sigil", [("n", [str(n) for n in SIG.IDS])], shapes, "*-0-north", "Stone", in_wall(),
                   "The crop-circle symbol carved over a Hub door (above c-4), face to the north. n is the sigil id"
                   " (docs/design/new-levels/hub-plan.md 4.3, tools/gen_hub_sigils.py): 0 the Hub's own, 1-18 the levels,"
                   " 20 the open door '178' (to 6.1), 21-44 dead doors; 19 is not built", "Carved Symbol")
    left = relief(sigilside_depths(), carve_tex, back_tex="carved")
    shapes = {"l": shape("sigilside-l", left), "r": shape("sigilside-r", mirror_x(left))}
    oriented_parts("hub-sigilside", [("part", ["l", "r"])], shapes, "*-l-north", "Stone", in_wall(),
                   "The carved border either side of a door's sigil (above l-4 and r-4), face to the north", "Carved Stone")


B15_SERVICE = True  # (B15) the service door's hinges and closer as geometry (False: B0's door)


def service_door():
    """Plain grey steel, 1 wide and 2 high (lower with a sill meeting the sidewalk, upper with a push bar, a small
    wired-glass window and the frame head), recessed in a steel frame."""
    def part(p):
        f = Face()
        w, z = 2.0, 1.0
        f.box("PostL", 0, w, 0, 16, -0.5, 16, "serviceframe")
        f.box("PostR", 16 - w, 16, 0, 16, -0.5, 16, "serviceframe")
        if p == "lower":
            f.box("Sill", w, 16 - w, 8, 16, -1.2, 16, "doorsill", faces=DIRS)
            f.box("Leaf", w, 16 - w, 0, 8, z, 16, "servicesteel", faces=DIRS)
            f.box("Kick", w + 0.5, 16 - w - 0.5, 3.5, 8, z - 0.3, z, "pushbar")
            if B15_SERVICE:  # (B15) the hinge's knuckles on the frame's edge
                for k in range(3):
                    f.box(f"Knuckle{k}", 1.7, 2.5, 0.6 + 1.3 * k, 1.8 + 1.3 * k, -1.1, -0.5, "pushbar")
        else:
            f.box("Head", 0, 16, 0, 2, -0.5, 16, "serviceframe")
            f.box("LeafSideL", w, 5.5, 2, 16, z, 16, "servicesteel")
            f.box("LeafSideR", 10.5, 16 - w, 2, 16, z, 16, "servicesteel")
            f.box("LeafAbove", 5.5, 10.5, 2, 3.5, z, 16, "servicesteel")
            f.box("LeafBelow", 5.5, 10.5, 8.5, 16, z, 16, "servicesteel")
            # A small wired-glass window in a real opening, its frame proud of the leaf
            f.box("Glass", 5.5, 10.5, 3.5, 8.5, z + 0.5, 16, "wireglass", faces=("north",))
            # (its inner faces a hair into the opening, not in the plane of the leaf's)
            f.box("WinT", 5, 11, 3, 3.55, z - 0.3, z + 0.5, "serviceframe")
            f.box("WinB", 5, 11, 8.45, 9, z - 0.3, z + 0.5, "serviceframe")
            f.box("WinL", 5, 5.55, 3.55, 8.45, z - 0.3, z + 0.5, "serviceframe")
            f.box("WinR", 10.45, 11, 3.55, 8.45, z - 0.3, z + 0.5, "serviceframe")
            # The push bar at hip height, on two brackets
            f.box("Bar", w + 1, 16 - w - 1, 11.6, 13.0, -1.6, -0.4, "pushbar")
            f.box("BracketL", w + 1, w + 2.2, 11.2, 13.4, -0.4, z, "serviceframe")
            f.box("BracketR", 16 - w - 2.2, 16 - w - 1, 11.2, 13.4, -0.4, z, "serviceframe")
            if B15_SERVICE:  # (B15) hinge knuckles, and the closer under the head with its arm
                for k in range(3):
                    f.box(f"Knuckle{k}", 1.7, 2.5, 4.0 + 1.3 * k, 5.2 + 1.3 * k, -1.1, -0.5, "pushbar")
                f.box("Closer", 2.5, 7.5, 2.05, 2.95, -0.7, z, "serviceframe")
                f.box("CloserArm", 7.5, 12.5, 2.3, 2.7, -0.5, 0.0, "pushbar")
                f.box("ArmShoe", 12.5, 13.4, 2.1, 2.9, -0.6, -0.5, "serviceframe")
        return f.els
    shapes = {p: shape(f"servicedoor-{p}", part(p)) for p in ("lower", "upper")}
    oriented_parts("hub-servicedoor", [("part", ["lower", "upper"])], shapes, "*-lower-north", "Metal",
                   in_wall(kind="locked", sounds=METAL),
                   "A plain grey steel service door, face to the north, 2 blocks high: lower (with a sill meeting the"
                   " sidewalk), upper (push bar, wired-glass window, frame head). Threshold kind locked: the way back out of"
                   " the Hub, opening only for whoever arrived beside it; also the Hub's entrance in Level 1, under"
                   " hub-sigil-0", "Service Door")


def ornate_doors():
    """The Tower's doors: dark oiled oak, 2 wide x 3 high, in a moulded stone frame; raised and fielded panels, bronze
    bands studded along, ring pulls near the meeting edge, a carved lunette fan across the top."""
    def l_part(row):
        def fn(u, v):
            if u < 2 or (row == 3 and v < 2):
                return 0.0  # the stone frame
            if row == 3:
                r = math.hypot(u - 16, v - 14)
                if r < 11:
                    if r >= 10:
                        return 0.5  # the lunette's rim
                    if r < 2.5:
                        return 0.5  # its hub
                    a = math.degrees(math.atan2(14 - v, 16 - u))
                    return 0.75 if (a % 15) < 4.5 else 1.5  # the rays of the fan
                return 1.0
            pu0, pu1 = 3.5, 14.0
            pv0, pv1 = (2.0, 14.0) if row == 2 else (2.0, 13.0)
            if pu0 <= u < pu1 and pv0 <= v < pv1:
                if pu0 + 1.5 <= u < pu1 - 1.5 and pv0 + 1.5 <= v < pv1 - 1.5:
                    return 0.25  # the raised field
                return 0.75  # its bevel
            return 1.0
        tex = {0.0: "ashlar-plain", 0.25: "oak-light", 0.5: "oak-light", 0.75: "oak", 1.0: "oak", 1.5: "oak"}
        els = relief(depth_grid(fn), lambda d: tex[d], back_tex="oak")
        # The stone frame stands a unit proud of the wall
        els.append(bx("FrameProud", (14, 0, -1), (16, 16, 0), "ashlar-plain", faces=FRONT))
        if row == 3:
            els.append(bx("HeadProud", (0, 14, -1), (14, 16, 0), "ashlar-plain", faces=FRONT))
        # A bronze band from the hinge side across the leaf, studded
        bv = {1: 3.0, 2: 9.5, 3: None}[row]
        if bv is not None:
            els.append(bx("Band", (0, 16 - bv - 1.4, -0.4), (14, 16 - bv, 1.0), "bronze", faces=FRONT))
            for i, u in enumerate((3, 5.5, 8, 10.5, 13)):
                x = 16 - u
                els.append(bx(f"Stud{i}", (x - 0.5, 16 - bv - 1.2, -0.9), (x + 0.5, 16 - bv - 0.2, -0.4), "bronze", faces=FRONT))
        if row == 2:
            # The ring pull near the meeting edge: a boss, and a ring hanging from it, tipped out a little
            els.append(bx("Boss", (1.6, 8.6, -0.6), (4.4, 11.4, 1.0), "bronze", faces=FRONT))
            for nm, frm, to in (("RingT", (1.5, 8.0, -1.2), (4.5, 8.6, -0.6)), ("RingB", (1.5, 3.8, -1.2), (4.5, 4.4, -0.6)),
                                ("RingL", (3.9, 4.4, -1.2), (4.5, 8.0, -0.6)), ("RingR", (1.5, 4.4, -1.2), (2.1, 8.0, -0.6))):
                els.append(bx(nm, frm, to, "bronze", rot=(-14, 0, 0), origin=(3, 8.6, -0.9)))
        return els
    shapes = {}
    for row in (1, 2, 3):
        left = l_part(row)
        shapes[f"l{row}"] = shape(f"ornatedoor-l{row}", left)
        shapes[f"r{row}"] = shape(f"ornatedoor-r{row}", mirror_x(left))
    groups = [("use", ["entrance", "forbidden"]), ("part", ["l1", "l2", "l3", "r1", "r2", "r3"])]
    by_use = {}
    for use in ("entrance", "forbidden"):
        for k, p in shapes.items():
            by_use[f"{use}-{k}"] = p
    fields = in_wall(sounds=WOOD)
    fields["behaviorsByType"] = {"*-entrance-*": [{"name": "BackroomsThreshold", "properties": {"kind": "towerdoor"}}],
                                 "*-forbidden-*": [{"name": "BackroomsThreshold", "properties": {"kind": "locked"}}]}
    oriented_parts("hub-ornatedoor", groups, by_use, "*-entrance-l1-north", "Wood", fields,
                   "The Tower's ornate double doors, 2 wide x 3 high (part l1-l3, r1-r3, rows from the bottom, l = the"
                   " viewer's left), face to the north, no sill (they stand on marble). entrance: threshold kind towerdoor"
                   " (the ten ways in); forbidden: kind locked, never linked (the rows of doors up the stair)", "Ornate Door")


def generate():
    carved_doors()
    sigils()
    service_door()
    ornate_doors()
