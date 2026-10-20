"""Level 1's props as geometry (graphics pass, "Level 1 props"), built with tools/modelkit.py: workbench, toolbox, steel
door, caution (wet floor) sign, power box with its conduit riser, breaker panel, drum, fire hose cabinet, fire
standpipe, fire alarm, security camera and fire extinguisher. Each function returns shape elements in
`detail_kit.bx`'s format; `gen_detail.level1` puts them into the wall decorations and props, and writes the drum
(whose block lives outside `detail/`). The textures are in `l1props_tex`.

Wall decorations are modelled on a wall's north face: z < 0 is out of the wall, z = 0 the wall, x grows toward the
west seen from the front (a north face shows u = 0 at x = 16). The block has the wall as its cube, so parts that
end on z = 0 leave their south face out.
"""
import math

import modelkit as K
from detail_kit import EXT, write_json, ASSETS, tpath
from gen_shapes import octagon, round_riser

import os

mat = K.mat
NOSOUTH = ("north", "east", "west", "up", "down")
SIDES4 = ("north", "east", "south", "west")

# Level 3's breaker and toggle, and Level 2's label, shared (their palettes sit well beside Level 1's grey)
EXT.update({"l3breaker": "backrooms:block/level3/breaker", "l3toggle": "backrooms:block/level3/toggle",
            "oildrum-rim": "backrooms:block/level2/oildrum-rim", "oildrum-side": "backrooms:block/level2/oildrum-side",
            "oildrum-top": "backrooms:block/level2/oildrum-top", "oildrum-label": "backrooms:block/level2/oildrum-label",
            "oildrum-bung": "backrooms:block/level2/oildrum-bung"})


def b(name, frm, to, tex, faces=K.DIRS, **kw):
    return K.box(name, frm, to, tex, faces=faces, **kw)


def wall(els):
    """Parts standing on the wall: no south face where the part ends on the wall (z = 0)."""
    for e in els:
        if e["to"][2] == 0 and "south" in e["faces"]:
            del e["faces"]["south"]
    return els


def disc(name, cx, cy, r, z1, z2, tex, faces=K.DIRS, lift=0.01):
    """A round plate facing north: an octagon of two crossed boxes and the same two turned 45 degrees about the axis.
    The four fronts are lifted a hair apart so they do not fight."""
    w = r * math.tan(math.radians(22.5))
    out = []
    zc = (z1 + z2) / 2
    for i, (hx, hy, rot) in enumerate(((r, w, 0), (w, r, 0), (r, w, 45), (w, r, 45))):
        out.append(b(f"{name}{i}", (cx - hx, cy - hy, z1 - lift * i), (cx + hx, cy + hy, z2), tex, faces,
                     rot=(0, 0, rot) if rot else None, origin=(cx, cy, zc)))
    return out


def ring8(name, cx, cz, a, y1, y2, t, tex, faces=("north", "up", "south")):
    """Eight plates round a vertical axis forming a ring `t` thick whose outer apothem is `a` (each faces out)."""
    side = 2 * a * math.tan(math.pi / 8) + 0.06
    return [b(f"{name}{k}", (cx - side / 2, y1, cz - a), (cx + side / 2, y2, cz - a + t), tex, faces,
              rot=(0, k * 45, 0) if k else None, origin=(cx, (y1 + y2) / 2, cz)) for k in range(8)]


# ---------------- Workbench and toolbox ----------------

def toolbox_parts(x0, y0, z0, w, h, d, name="Tb", handle=True):
    """A red steel toolbox with its front to the north: a bevelled body and lid, ribs on the lid, a carry handle on two
    posts, two latches over the lid's lip and two hinges at the back."""
    body_h = h * 0.72
    els = K.bevelled_box(name + "Body", (x0, y0, z0), (x0 + w, y0 + body_h, z0 + d), "l1toolred", b=0.25)
    els += K.bevelled_box(name + "Lid", (x0 - 0.25, y0 + body_h, z0 - 0.25), (x0 + w + 0.25, y0 + h, z0 + d + 0.25), "l1toolred2", b=0.25)
    lw = w - 3.0
    for i, zz in enumerate((z0 + d * 0.3, z0 + d * 0.7)):  # ribs pressed in the lid
        els.append(b(f"{name}Rib{i}", (x0 + 1.5, y0 + h, zz - 0.2), (x0 + 1.5 + lw, y0 + h + 0.25, zz + 0.2), "l1toolred", faces=("north", "south", "up", "east", "west")))
    for i, fx in enumerate((x0 + w * 0.2, x0 + w * 0.8 - 1.6)):
        els.append(b(f"{name}Catch{i}", (fx, y0 + body_h - 2.3, z0 - 0.4), (fx + 1.6, y0 + body_h - 0.3, z0), "l1steel", faces=NOSOUTH))
        els.append(b(f"{name}Hasp{i}", (fx + 0.2, y0 + body_h - 0.3, z0 - 0.65), (fx + 1.4, y0 + body_h + 1.2, z0 - 0.25), "l1steel", faces=NOSOUTH))
        els.append(b(f"{name}Hinge{i}", (fx, y0 + body_h - 1.0, z0 + d), (fx + 1.6, y0 + body_h + 0.8, z0 + d + 0.4), "l1steeldark", faces=("south", "up", "east", "west")))
    if handle:
        px1, px2 = x0 + w * 0.3, x0 + w * 0.7
        zc = z0 + d / 2
        for i, px in enumerate((px1, px2)):
            els.append(b(f"{name}Post{i}", (px - 0.3, y0 + h, zc - 0.4), (px + 0.3, y0 + h + 1.0, zc + 0.4), "l1iron"))
        els.append(b(f"{name}Grip", (px1 - 0.45, y0 + h + 0.7, zc - 0.5), (px2 + 0.45, y0 + h + 1.4, zc + 0.5), "l1black"))
    return els


def toolbox():
    return toolbox_parts(3, 0, 5, 10, 7, 6)


def workbench():
    top = mat(top="l1benchtop", side="l1woodh", bottom="l1wood")
    els = K.bevelled_box("Top", (0, 13, 1.5), (16, 15, 14), top, b=0.25)
    for name, x, z in (("LegFL", 1.75, 3.5), ("LegFR", 14.25, 3.5), ("LegBL", 1.75, 12.5), ("LegBR", 14.25, 12.5)):
        els += K.leg(name, x, z, 0, 13, t=2.0, tex="l1wood", foot=0.5)
    # aprons under the top, and the shelf's rails
    els += [b("ApronF", (2.75, 10.5, 2.75), (13.25, 13, 3.75), "l1wood", faces=("north", "south", "down")),
            b("ApronB", (2.75, 10.5, 11.75), (13.25, 13, 12.75), "l1wood", faces=("north", "south", "down")),
            b("ApronL", (0.75, 10.5, 4.5), (1.75, 13, 11.5), "l1wood", faces=("west", "down", "north", "south")),
            b("ApronR", (14.25, 10.5, 4.5), (15.25, 13, 11.5), "l1wood", faces=("east", "down", "north", "south")),
            b("RailF", (2.75, 2.0, 2.75), (13.25, 3.0, 3.75), "l1wood", faces=("north", "south", "down")),
            b("RailB", (2.75, 2.0, 11.75), (13.25, 3.0, 12.75), "l1wood", faces=("north", "south", "down")),
            b("Shelf", (1.5, 3, 3.0), (14.5, 4, 13.0), mat(top="l1ply", all="l1ply"))]
    els += toolbox_parts(4, 4, 5.5, 7, 4.2, 4.6, name="Shelf", handle=False)
    # the pegboard, in a frame of timber
    els += [b("Peg", (1, 15, 13.5), (15, 30, 14.5), mat(front="l1peg", all="l1wood"), faces=("north",)),
            b("PegFrameL", (0.05, 15, 13.25), (1, 31, 15), "l1wood", faces=("north", "east", "west", "up")),
            b("PegFrameR", (15, 15, 13.25), (15.95, 31, 15), "l1wood", faces=("north", "east", "west", "up")),
            b("PegFrameT", (1, 30, 13.25), (15, 31, 15), "l1wood", faces=("north", "up", "down")),
            b("PegBack", (1, 15, 14.5), (15, 30, 15), "l1wood", faces=("south",))]
    # tools on it: a hammer, a screwdriver, a spanner and a coil of cord (they hang on pegs, 1 unit off the board)
    els += [b("HammerHandle", (11.6, 19, 12.6), (12.4, 26, 13.5), "l1wood", faces=("north", "east", "west", "up")),
            b("HammerHead", (10.6, 25.2, 12.4), (13.4, 26.8, 13.5), "l1iron", faces=("north", "east", "west", "up", "down")),
            b("DriverHandle", (8.0, 22, 12.5), (9.4, 26.5, 13.5), "l1toolred", faces=("north", "east", "west", "up", "down")),
            b("DriverShaft", (8.4, 17.5, 12.9), (9.0, 22, 13.5), "l1steel", faces=("north", "east", "west", "down")),
            b("Spanner", (5.0, 18, 12.8), (6.4, 26.5, 13.5), "l1steel", faces=("north", "east", "west", "down")),
            b("SpannerJaw", (4.4, 26.5, 12.8), (7.0, 28, 13.5), "l1steel", faces=("north", "east", "west", "up")),
            b("SpannerNotch", (5.1, 27.0, 12.7), (6.3, 28.1, 13.5), "l1seam", faces=("north",))]
    els += disc("Cord", 2.5, 22, 2.0, 12.6, 13.5, "l1cord", faces=("north", "east", "west", "up", "down"))
    # a vise on the front right corner, its screw and bar pointing at the bench's user
    els += [b("ViseBase", (12.5, 15, 3.2), (15, 16.3, 7.2), "l1iron"),
            b("ViseFixed", (12.5, 16.3, 3.2), (15, 18.8, 5.2), "l1iron"),
            b("ViseJaw", (12.8, 16.3, 1.9), (14.7, 18.5, 3.0), "l1iron"),
            b("ViseGuide", (13.45, 16.9, 3.0), (14.05, 17.5, 3.2), "l1steel", faces=("north", "up")),
            b("ViseScrew", (13.5, 16.9, 0.6), (14.0, 17.5, 1.9), "l1steel"),
            b("ViseBar", (12.4, 16.95, 0.3), (15.1, 17.45, 0.8), "l1steeldark")]
    els += [b("Hammer", (5, 15, 5), (10, 15.8, 6), "l1wood"), b("HammerOnHead", (9.5, 15, 4.5), (11, 16.4, 6.5), "l1iron")]
    return els


# ---------------- The steel door ----------------

def steel_door(part):
    """The locked steel door as a cube leaf with its hardware, on all four sides (the block has no facing; on the two
    that meet the jambs the hardware is buried in the wall, as the tunnel doors' B5): a raised frame round the leaf, a
    push bar, kick plate, two hinges and a lock on the lower; on the upper a steel bead round dark wired glass (set
    just proud of the leaf) and the NO ENTRY plate. Everything stops 0.05 short of the block's sides."""
    fr = "l1doorframe"
    hw = [b("StileL", (0.05, 0, -0.5), (1.55, 16, 0), fr, faces=("north", "east", "west") + (() if part == "upper" else ("down",))),
          b("StileR", (14.45, 0, -0.5), (15.95, 16, 0), fr, faces=("north", "east", "west") + (() if part == "upper" else ("down",)))]
    if part == "lower":
        hw.append(b("RailB", (1.55, 0, -0.5), (14.45, 1.5, 0), fr, faces=("north", "up")))
        hw += K.push_bar("Bar", 2.5, 12.5, 11.0, 0, tex="l1steel", bar_tex="l1steel")
        hw += K.kick_plate("Kick", 2.5, 13.5, 2.0, 6.5, 0, tex="l1steel")
        hw += K.hinge("HingeA", 15.2, 2.5, 5.5, 0, tex="l1steeldark", side="right")
        hw += K.hinge("HingeB", 15.2, 10.0, 13.0, 0, tex="l1steeldark", side="right")
        hw.append(b("LockPlate", (2.5, 6.6, -0.5), (4.1, 9.4, 0), "l1steeldark", faces=NOSOUTH))
        hw.append(b("LockCyl", (2.95, 7.4, -0.8), (3.65, 8.6, -0.5), "brass", faces=NOSOUTH))
    else:
        hw.append(b("RailT", (1.55, 14.5, -0.5), (14.45, 16, 0), fr, faces=("north", "down")))
        bead, _ = K.frame_members("Bead", 4.5, 9.6, 11.5, 14.25, -0.75, 0, 0.5, fr)
        for e in bead:
            e["faces"].pop("south", None)
        hw += bead
        hw.append(b("Glass", (5, 10.1, -0.35), (11, 13.75, -0.2), "l1wired", faces=("north",)))
        hw.append(b("Plate", (1.75, 1.0, -0.5), (14.25, 9.0, 0), mat(front="l1doorplate", all="l1steeldark"), faces=NOSOUTH, uv=[0, 0, 12.5, 16]))
        hw += K.hinge("HingeA", 15.2, 10.0, 13.0, 0, tex="l1steeldark", side="right")
    els = [b("Leaf", (0, 0, 0), (16, 16, 16), f"metaldoor-{part}", uv=[0, 0, 16, 16])]
    for i in range(4):
        els += [dict(e, name=f"{e['name']}{i}") for e in K.turn(wall(hw), i)]
    return els


# ---------------- The caution sign ----------------

def caution_sign():
    """A folding wet-floor sign: two yellow panels with pressed edges leaning on a hinge, rubber feet, a grip across the
    top. The CAUTION / WET FLOOR face is printed in a pixel face, a figure losing its footing under it."""
    els = []
    for nm, z1, z2, rx, face, back in (("N", 6.45, 7.05, 12, "north", "south"), ("S", 8.95, 9.55, -12, "south", "north")):
        org = (8, 15, 8)
        faces = {face: "l1signface", back: "l1yellow", "east": "l1yellow", "west": "l1yellow", "up": "l1yellow", "down": "l1yellow"}
        els.append(b(f"Panel{nm}", (1, 0.8, z1), (15, 14.6, z2), faces, rot=(rx, 0, 0), origin=org))
        els.append(b(f"Skirt{nm}", (1.7, 0.2, z1 + 0.1), (14.3, 0.8, z2 - 0.1), "l1yellow", rot=(rx, 0, 0), origin=org))
        for i, fx in enumerate((1.5, 12.5)):
            els.append(b(f"Foot{nm}{i}", (fx, 0, z1 - 0.1), (fx + 2, 0.8, z2 + 0.1), "l1black", rot=(rx, 0, 0), origin=org))
        els.append(b(f"Cap{nm}", (3, 14.6, z1 + 0.05), (13, 15.4, z2 - 0.05), "l1yellow", rot=(rx, 0, 0), origin=org))
    els.append(b("Hinge", (5.5, 14.4, 7.4), (10.5, 15.6, 8.6), "l1black"))
    return els


# ---------------- Wall decorations ----------------

def power_box():
    """Rel 2: a grey enclosure with a framed door on a hinge, a quarter-turn latch and a warning decal, a gland and
    conduit with a clamp up the top, and a small disconnect switch box on its side joined by a nipple."""
    els = [b("Body", (3, 2, -2.5), (11, 12, 0), mat(all="l1grey", front="l1seam"), faces=NOSOUTH)]
    els += K.bevelled_box("Door", (3.25, 2.25, -3.1), (10.75, 11.75, -2.5), "l1grey", b=0.25)
    els += K.hinge("HingeA", 10.75, 2.9, 4.5, -3.1, tex="l1steeldark", side="right")
    els += K.hinge("HingeB", 10.75, 9.3, 10.9, -3.1, tex="l1steeldark", side="right")
    els.append(b("LatchPlate", (3.7, 4.0, -3.35), (5.5, 5.6, -3.1), "l1steel", faces=NOSOUTH))
    els += K.knob("Latch", 4.6, 4.8, -3.35, r=0.5, depth=0.9, tex="l1steeldark")
    els.append(b("LatchWing", (3.8, 4.6, -4.55), (5.4, 5.0, -4.2), "l1steeldark"))
    els.append(b("Decal", (4.4, 6.2, -3.25), (9.4, 10.7, -3.1), mat(front="l1decal", all="l1yellow"), faces=NOSOUTH))
    els.append(b("Gland", (5.9, 12, -2.1), (8.1, 12.75, -0.4), "l1steeldark", faces=SIDES4 + ("up",)))
    els += conduit_run("Con", 12.75, 16)
    els.append(b("ClampRing", (6.0, 14.2, -2.15), (8.0, 14.9, -0.35), "l1steel", faces=SIDES4))
    els.append(b("ClampSaddle", (6.5, 14.2, -0.4), (7.5, 14.9, 0), "l1steel", faces=NOSOUTH))
    # the disconnect switch beside it
    els.append(b("Small", (12, 4, -2.0), (15, 10, 0), mat(all="l1greydark", front="l1grey"), faces=NOSOUTH))
    els.append(b("SmallPlate", (12.25, 4.25, -2.4), (14.75, 9.75, -2.0), "l1grey", faces=NOSOUTH))
    els.append(b("Toggle", (13.0, 5.2, -3.1), (14.0, 8.4, -2.4), "l1red"))
    els.append(b("Nipple", (11, 6.6, -1.9), (12, 7.6, -0.9), "l1steel", faces=("north", "south", "up", "down")))
    return els


def conduit_run(name, y1, y2, xc=7.0, zc=-1.25):
    """A round conduit (two crossed boxes, 1.5 across) from y1 to y2 at (xc, zc)."""
    return [b(name + "A", (xc - 0.75, y1, zc - 0.6), (xc + 0.75, y2, zc + 0.6), "l1steel", faces=SIDES4),
            b(name + "B", (xc - 0.6, y1, zc - 0.75), (xc + 0.6, y2, zc + 0.75), "l1steel", faces=SIDES4)]


def power_riser3():
    """Rel 3: the conduit goes on up the wall on a clamp at mid height."""
    els = conduit_run("Con", 0, 16)
    els.append(b("ClampRing", (6.0, 7.2, -2.15), (8.0, 7.9, -0.35), "l1steel", faces=SIDES4))
    els.append(b("ClampSaddle", (6.5, 7.2, -0.4), (7.5, 7.9, 0), "l1steel", faces=NOSOUTH))
    return els


def power_riser4():
    """Rel 4, under the ceiling slab: the conduit ends in a junction box bolted to the ceiling (a cover on four screws),
    with a second stub leaving its side along the ceiling and capped."""
    els = conduit_run("Con", 0, 12.25)
    els.append(b("ClampRing", (6.0, 5.0, -2.15), (8.0, 5.7, -0.35), "l1steel", faces=SIDES4))
    els.append(b("ClampSaddle", (6.5, 5.0, -0.4), (7.5, 5.7, 0), "l1steel", faces=NOSOUTH))
    els.append(b("Box", (5.0, 12.25, -2.5), (9.0, 16, 0), mat(all="l1greydark", front="l1grey"), faces=("north", "east", "west", "down")))
    els.append(b("Cover", (5.4, 12.65, -3.0), (8.6, 15.6, -2.5), "l1grey", faces=("north", "east", "west", "up", "down")))
    for i, (sx, sy) in enumerate(((5.6, 12.85), (8.0, 12.85), (5.6, 14.8), (8.0, 14.8))):
        els.append(b(f"Screw{i}", (sx, sy, -3.2), (sx + 0.5, sy + 0.5, -3.0), "l1steeldark", faces=("north", "up", "east", "west", "down")))
    els.append(b("Stub", (9.0, 13.6, -1.85), (11.5, 15.0, -0.65), "l1steel", faces=("north", "up", "down", "east")))
    els.append(b("StubCap", (11.5, 13.45, -2.0), (12.1, 15.15, -0.5), "l1steeldark", faces=("north", "up", "down", "east")))
    return els


def breaker_panel():
    """A main breaker panel: a grey enamel box with a raised rim round a dead front, two columns of six bakelite
    breakers either side of a bus cover (two tripped), a label plate and a warning decal, a red main-switch handle on
    its side, and a conduit coming up into a conduit body (a fitting with a screwed cover) that sits against the wall
    above, where the run enters it (as Level 3's panel, in Level 1's grey)."""
    FRONT = ("north", "east", "west", "up", "down")
    els = [b("Box", (2, 0.5, -2.5), (14, 13.0, 0), mat(all="l1grey", front="l1seam"), faces=FRONT)]
    rim, _ = K.frame_members("Rim", 2, 0.5, 14, 13.0, -3.0, -2.5, 0.75, "l1grey")
    for e in rim:
        e["faces"].pop("south", None)
    els += rim
    els.append(b("Bus", (7.5, 2.5, -2.85), (8.5, 10.0, -2.5), "l1greydark", faces=FRONT))
    tripped = {2, 8}
    for col, cx in enumerate((4.9, 11.1)):
        inward = 1 if col == 0 else -1
        for row in range(6):
            k, y = col * 6 + row, 2.75 + row * 1.35
            els.append(b(f"Breaker{k}", (cx - 1.5, y - 0.5, -3.0), (cx + 1.5, y + 0.45, -2.5), "l3breaker", faces=FRONT))
            tx = cx + 0.5 * (-inward if k in tripped else inward)
            els.append(b(f"Toggle{k}", (tx - 0.4, y - 0.2, -3.45), (tx + 0.4, y + 0.2, -3.0), "l3toggle", faces=FRONT))
    els.append(b("Label", (4.0, 10.6, -2.75), (12.0, 12.1, -2.5), mat(front="cablabel", all="l1white"), faces=FRONT))
    els.append(b("Warn", (3.2, 0.9, -2.75), (5.2, 2.1, -2.5), mat(front="warn3", all="l1yellow"), faces=FRONT))
    els.append(b("SwitchBoss", (14, 6.5, -2.0), (14.75, 9.0, -0.5), "l1grey", faces=("north", "east", "up", "down")))
    els.append(b("SwitchHandle", (14.75, 7.25, -1.75), (15.5, 11.5, -0.75), "l1red"))
    # the conduit: a gland on the top, a run up, and a conduit body with a cover under the ceiling of this block
    els.append(b("Gland", (6.5, 13.0, -2.0), (8.5, 13.6, -0.5), "l1steeldark", faces=SIDES4 + ("up",)))
    els += conduit_run("Con", 13.6, 14.4, xc=7.5, zc=-1.25)
    els.append(b("CBody", (6.5, 14.4, -2.25), (8.5, 16, 0), "l1steeldark", faces=("north", "east", "west", "down")))
    els.append(b("CCover", (6.75, 14.65, -2.7), (8.25, 15.75, -2.25), "l1steel", faces=NOSOUTH))
    for i, sy in enumerate((14.85, 15.3)):
        els.append(b(f"CScrew{i}", (7.25, sy, -2.85), (7.75, sy + 0.3, -2.7), "l1steeldark", faces=("north", "up", "east", "west", "down")))
    return els


def extinguisher():
    """A wall-mounted dry-powder extinguisher: a red octagonal cylinder with a domed shoulder, a printed label, two
    straps and a backplate on the wall, a brass valve and neck, a pressure gauge, a handle and squeeze lever with
    its pin, the hose looped down to a nozzle clipped on the side, and the ISO sign over it."""
    cx, cz, a = 8.0, -2.5, 2.25
    els = [b("Plate", (6.5, 2.5, -0.35), (9.5, 8.0, 0), "l1steeldark", faces=NOSOUTH)]
    els += octagon("Body", cx, cz, a, 0.25, 8.5, "l1red", faces=SIDES4)
    els += octagon("Shoulder", cx, cz, a - 0.55, 8.5, 9.4, "l1red", faces=SIDES4 + ("up",), lift=0.01)
    els += octagon("Base", cx, cz, a + 0.1, 0.0, 0.6, "l1iron", faces=SIDES4 + ("down",), lift=0.01)
    els += octagon("StrapLo", cx, cz, a + 0.2, 2.5, 3.4, "l1steeldark", faces=SIDES4 + ("up", "down"), lift=0.01)
    els += octagon("StrapHi", cx, cz, a + 0.2, 6.3, 7.2, "l1steeldark", faces=SIDES4 + ("up", "down"), lift=0.01)
    els.append(b("Label", (7.1, 3.8, -4.85), (8.9, 6.0, -4.75), mat(front="l1white", all="l1white"), faces=("north",)))
    els.append(b("LabelBar", (7.1, 5.2, -4.88), (8.9, 5.7, -4.8), "l1black", faces=("north",)))
    els += [b("Neck", (7.3, 9.4, -3.2), (8.7, 10.2, -1.8), "brass", faces=SIDES4),
            b("Valve", (6.8, 10.0, -3.9), (9.4, 11.4, -1.7), "brass"),
            b("Handle", (6.7, 11.4, -4.3), (9.4, 12.0, -2.0), "l1iron"),
            b("Lever", (6.9, 10.3, -4.6), (8.8, 10.9, -3.9), "l1iron"),
            b("Pin", (9.4, 10.6, -3.3), (10.2, 11.0, -2.9), "l1steel", faces=("north", "up", "down", "east"))]
    els += K.dial("Gauge", 8.0, 10.7, -3.9, r=1.0, face="l1dial", bezel="brass", needle="l1black")
    els += [b("HoseTop", (9.4, 10.1, -3.8), (10.7, 10.8, -3.15), "l1black"),
            b("HoseRun", (10.0, 5.0, -3.9), (10.8, 10.8, -3.1), "l1black"),
            b("Nozzle", (9.8, 3.8, -4.1), (11.2, 5.0, -2.9), "l1iron"),
            b("Clip", (9.9, 6.4, -3.1), (10.9, 7.2, -2.5), "l1steeldark", faces=NOSOUTH[:2] + ("up",))]
    els.append(b("Sign", (6.25, 12.4, -0.4), (9.75, 15.9, 0), mat(front="l1extsign", all="l1red"), faces=NOSOUTH))
    return els


def fire_alarm():
    """A pull station: a red box with a label strip, a white lever (PULL) on a hinge with a tab, and over it a fire
    bell on a stem, a gong stud on its dome."""
    els = K.bevelled_box("Box", (4, 2.5, -1.75), (12, 12, 0), "l1red", b=0.25)
    els.append(b("Label", (4.25, 8.4, -2.1), (11.75, 11.4, -1.75), "l1firelabel", faces=NOSOUTH))
    els.append(b("Hinge", (4.25, 3.1, -2.6), (11.75, 3.6, -2.1), "l1steeldark", faces=NOSOUTH))
    els.append(b("Lever", (4.25, 3.6, -2.5), (11.75, 8.0, -2.1), mat(front="l1pull", all="l1white"), faces=NOSOUTH))
    els.append(b("Tab", (6.5, 2.3, -2.7), (9.5, 3.1, -2.2), "l1white", faces=NOSOUTH))
    els.append(b("Stem", (7.4, 12.0, -1.4), (8.6, 12.8, -0.2), "l1steeldark", faces=SIDES4))
    els += octagon("Bell", 8.0, -1.6, 2.4, 12.8, 13.8, "l1red", faces=SIDES4, lift=0.01)
    els += octagon("BellDome", 8.0, -1.6, 1.7, 13.8, 14.6, "l1red", faces=SIDES4 + ("up",), lift=0.01)
    els.append(b("Gong", (7.6, 14.6, -2.0), (8.4, 15.4, -1.2), "l1steel", faces=SIDES4 + ("up",)))
    els.append(b("Skirt", (5.2, 12.5, -3.0), (10.8, 12.8, -0.2), "l1reddark", faces=("north", "east", "west", "down")))
    return els


def hose_cabinet():
    """A fire hose cabinet: a red tub on the wall, a hose reel inside (a back flange, a coil of flax-white hose, a hub),
    the hose run to a brass nozzle on a bracket and a red handwheel valve; a framed door with a HOSE plate, a pane of
    glass (cut out, with glints and dust), hinges and a latch."""
    els = [b("Back", (2.75, 0.75, -0.5), (13.25, 13.25, 0), "l1greydark", faces=("north",)),
           b("TubL", (2, 0, -3), (2.75, 14, 0), "l1red", faces=NOSOUTH),
           b("TubR", (13.25, 0, -3), (14, 14, 0), "l1red", faces=NOSOUTH),
           b("TubT", (2.75, 13.25, -3), (13.25, 14, 0), "l1red", faces=NOSOUTH),
           b("TubB", (2.75, 0, -3), (13.25, 0.75, 0), "l1red", faces=NOSOUTH)]
    cx, cy = 8.0, 7.25
    els += disc("ReelBack", cx, cy, 4.5, -1.2, -0.5, "l1steeldark", faces=("north", "east", "west", "up", "down"))
    els += disc("Coil", cx, cy, 4.0, -2.3, -1.2, "l1hose", faces=("north", "east", "west", "up", "down"))
    els += disc("Hub", cx, cy, 1.3, -2.8, -2.3, "l1steel", faces=("north", "east", "west", "up", "down"))
    els += [b("HoseRun", (3.5, 3.2, -2.3), (4.5, 6.2, -1.3), "l1hose", faces=("north", "east", "west", "down")),
            b("Nozzle", (3.1, 1.6, -2.5), (4.9, 3.2, -1.1), "brass"),
            b("Bracket", (2.75, 1.0, -1.6), (3.1, 3.8, -1.0), "l1steeldark", faces=("north", "up", "east")),
            b("Pipe", (11.0, 6.6, -1.7), (12.2, 7.9, -0.5), "brass", faces=SIDES4 + ("up",)),
            b("Valve", (10.8, 9.2, -2.4), (12.8, 11.3, -1.0), "brass")]
    els += disc("Wheel", 11.8, 12.2, 1.4, -3.0, -2.6, "l1red", faces=("north", "east", "west", "up", "down"))
    els.append(b("Stem", (11.55, 11.3, -2.6), (12.05, 11.9, -2.2), "l1steel", faces=SIDES4))
    # the door
    z1, z2 = -3.75, -3.0
    els += [b("DoorB", (2, 0, z1), (14, 1.25, z2), "l1red", faces=NOSOUTH),
            b("DoorT", (2, 11, z1), (14, 14, z2), "l1red", faces=NOSOUTH),
            b("DoorL", (2, 1.25, z1), (3.25, 11, z2), "l1red", faces=("north", "east", "west")),
            b("DoorR", (12.75, 1.25, z1), (14, 11, z2), "l1red", faces=("north", "east", "west")),
            b("Pane", (3.25, 1.25, -3.5), (12.75, 11, -3.4), "l1cabglass", faces=("north",)),
            b("Name", (3.0, 11.0, -3.95), (13.0, 14.0, -3.75), "l1hoselabel", faces=("north", "up"))]
    els += K.hinge("HingeA", 14, 2.2, 4.0, z1, tex="l1steeldark", side="right")
    els += K.hinge("HingeB", 14, 8.0, 9.8, z1, tex="l1steeldark", side="right")
    els += K.knob("Latch", 3.2, 6.2, z1, r=0.6, depth=1.0, tex="l1steel")
    return els


def standpipe(rel):
    """A fire standpipe riser in red, round (`gen_shapes.round_riser` in its own skin), standing off the wall on clamps.
    Rel 1: a floor flange, a gate valve with a handwheel, a brass hose outlet with its coupling and a cap hung on a
    chain. Rel 2: a pipe clamp on a standoff. Rel 3 and 4: a flanged coupling; rel 4 ends in a ceiling flange."""
    xc, zc, r = 8.0, -2.4, 1.75
    els = round_riser("Pipe", xc, zc, r, "l1riserred", 0, 16)
    if rel == 1:
        els += round_riser("Foot", xc, zc, 2.6, "flange", 0, 0.75, shaded=False, faces=("up",))
        els.append(b("Valve", (6.9, 8.4, zc - 1.9), (9.1, 10.6, zc + 1.9), "brass", faces=SIDES4))
        els.append(b("Bonnet", (7.4, 10.6, zc - 1.0), (8.6, 12.0, zc + 1.0), "brass", faces=SIDES4))
        els.append(b("Stem", (7.8, 12.0, zc - 0.2), (8.2, 13.0, zc + 0.2), "l1steel", faces=SIDES4))
        els += octagon("Wheel", xc, zc, 1.9, 13.0, 13.5, "l1red", faces=SIDES4 + ("up", "down"), lift=0.01)
        els.append(b("Stub", (7.0, 3.8, -5.0), (9.0, 5.8, zc), "brass", faces=("north", "east", "west", "up", "down")))
        els.append(b("Nut", (6.5, 3.4, -6.5), (9.5, 6.2, -5.0), "brass"))
        els.append(b("Cap", (6.9, 3.8, -7.2), (9.1, 5.8, -6.5), "brass"))
        for i in range(4):  # the cap's chain hangs down to a ring on the pipe
            els.append(b(f"Link{i}", (9.6, 5.4 - i * 0.7, -6.6 + i * 0.3), (10.1, 5.9 - i * 0.7, -6.1 + i * 0.3), "l1steeldark"))
    elif rel == 2:
        els += round_riser("Clamp", xc, zc, 2.2, "flange", 7.5, 8.7, shaded=False, faces=("up", "down"))
        els.append(b("Standoff", (7, 7.5, zc + 1.0), (9, 8.7, 0), "flange", faces=("north", "east", "west", "up", "down")))
    else:
        els += round_riser("Flange", xc, zc, 2.5, "flange", 7.5, 8.4, shaded=False, faces=("up", "down"))
        els += round_riser("Collar", xc, zc, 2.0, "flange", 8.4, 9.2, shaded=False, faces=("up",))
        els.append(b("Standoff", (7, 3.0, zc + 1.0), (9, 4.2, 0), "flange", faces=("north", "east", "west", "up", "down")))
        els += round_riser("Clamp", xc, zc, 2.2, "flange", 3.0, 4.2, shaded=False, faces=("up", "down"))
        if rel == 4:
            els += round_riser("Ceil", xc, zc, 2.9, "flange", 15.1, 16, shaded=False, faces=("down",))
    return els


def camera():
    """A security camera on a wall: a plate with an arm and swivel joint, a bullet housing hanging under a sun hood with
    side flaps, a round lens (a bezel ring and a black glass dome), a cable boot at the back. It has not worked in a
    long time; the paint is grubby."""
    els = [b("Plate", (5.0, 8.5, -0.6), (11.0, 14.0, 0), "l1camdark", faces=NOSOUTH),
           b("Arm", (6.75, 10.4, -5.0), (9.25, 12.4, -0.6), "l1camdark", faces=("north", "east", "west", "up", "down", "south")),
           b("Swivel", (7.0, 9.3, -5.4), (9.0, 10.4, -3.4), "l1camdark")]
    for i, (sx, sy) in enumerate(((5.4, 13.2), (10.0, 13.2), (5.4, 9.0), (10.0, 9.0))):
        els.append(b(f"Bolt{i}", (sx, sy, -0.9), (sx + 0.6, sy + 0.6, -0.6), "l1steeldark", faces=NOSOUTH))
    els += K.bevelled_box("Housing", (6, 4.5, -10), (10, 8.5, -3), "l1cambody", b=0.25)
    els.append(b("Hood", (5.25, 8.5, -10.8), (10.75, 9.2, -3.2), "l1cambody"))
    els.append(b("HoodLipL", (5.25, 8.0, -10.8), (5.75, 8.5, -3.6), "l1cambody", faces=("north", "east", "west", "down", "south")))
    els.append(b("HoodLipR", (10.25, 8.0, -10.8), (10.75, 8.5, -3.6), "l1cambody", faces=("north", "east", "west", "down", "south")))
    els += disc("Bezel", 8.0, 6.5, 1.55, -10.6, -10.0, "l1camdark", faces=("north", "east", "west", "up", "down"))
    els += disc("Lens", 8.0, 6.5, 1.1, -10.95, -10.6, "l1camlens", faces=("north", "east", "west", "up", "down"))
    els.append(b("Boot", (7.2, 5.6, -3.0), (8.8, 7.4, -2.2), "l1camdark", faces=("south", "up", "down", "east", "west")))
    return els


# ---------------- The drum ----------------

def facets(name, cx, cz, a, y1, y2, tex, wcol=5.5, t=0.05):
    """The eight faces of an octagonal prism, one thin plate per facet: each its own window of the wall texture,
    `wcol` units across and three columns apart round the drum, so neighbouring facets differ."""
    w = a * math.tan(math.radians(22.5))
    out = []
    hh = round(min(16.0, (y2 - y1)), 3)
    for k in range(8):
        axis, diag = k // 2, k % 2
        if axis == 0:
            frm, to, face = (cx - w, y1, cz - a), (cx + w, y2, cz - a + t), "north"
        elif axis == 1:
            frm, to, face = (cx + a - t, y1, cz - w), (cx + a, y2, cz + w), "east"
        elif axis == 2:
            frm, to, face = (cx - w, y1, cz + a - t), (cx + w, y2, cz + a), "south"
        else:
            frm, to, face = (cx - a, y1, cz - w), (cx - a + t, y2, cz + w), "west"
        u0 = wcol * ((k * 2 + k // 3) % 3)
        out.append(b(f"{name}{k}", frm, to, tex, (face,), uv=[u0, 0, round(u0 + 2 * w, 3), hh],
                     rot=(0, 45, 0) if diag else None, origin=(cx, y1, cz)))
    return out


def drum_shape():
    """An eight-sided steel drum on its 12 x 12 footprint: a wall of eight plates, two raised hoops, a rolled chime top
    and bottom, a pressed lid with a bung and a vent plug, and a paper label on the north side."""
    cx, cz, a = 8.0, 8.0, 6.0
    side, top, rim = "oildrum-side", "oildrum-top", "oildrum-rim"
    els = facets("Wall", cx, cz, a, 0.9, 13.5, side)
    els += ring8("Hoop1", cx, cz, a + 0.4, 3.0, 3.9, 0.4, rim, faces=("north", "up", "down"))
    els += ring8("Hoop2", cx, cz, a + 0.4, 11.0, 11.9, 0.4, rim, faces=("north", "up", "down"))
    els += ring8("ChimeLo", cx, cz, a + 0.35, 0.0, 0.9, 0.5, rim, faces=("north", "up"))
    els += ring8("ChimeHi", cx, cz, a + 0.4, 13.4, 15.0, 0.6, rim, faces=("north", "up", "south"))
    lid = octagon("Lid", cx, cz, 5.85, 13.5, 14.45, top, faces=SIDES4 + ("up",), lift=0.01)
    for e in lid:  # each box's lid face takes the middle of the pressed top: it is the same ring whichever way it is turned
        hx, hz = (e["to"][0] - e["from"][0]) / 2, (e["to"][2] - e["from"][2]) / 2
        e["faces"]["up"]["uv"] = [round(8 - hx, 3), round(8 - hz, 3), round(8 + hx, 3), round(8 + hz, 3)]
    els += lid
    els += octagon("BungFlange", 9.8, 5.8, 1.1, 14.45, 14.75, "oildrum-bung", faces=SIDES4 + ("up",), lift=0.01)
    els += octagon("Bung", 9.8, 5.8, 0.7, 14.75, 15.1, "oildrum-bung", faces=SIDES4 + ("up",), lift=0.01)
    els.append(b("BungSlot", (9.55, 15.1, 5.7), (10.05, 15.15, 5.9), "l1seam", faces=("up",)))
    els += octagon("VentFlange", 6.0, 10.4, 0.8, 14.45, 14.7, "oildrum-bung", faces=SIDES4 + ("up",), lift=0.01)
    els += octagon("Vent", 6.0, 10.4, 0.45, 14.7, 15.0, "oildrum-bung", faces=SIDES4 + ("up",), lift=0.01)
    els.append(b("Label", (5.5, 5.0, 1.55), (10.5, 11.0, 1.85), mat(front="oildrum-label", all="oildrum-label"), faces=("north",)))
    return els


def write_drum():
    els = drum_shape()
    keys = sorted({f["texture"][1:] for e in els for f in e["faces"].values()})
    data = {"textureWidth": 16, "textureHeight": 16, "textures": {k: tpath(k) for k in keys}, "elements": els}
    path = os.path.join(ASSETS, "shapes", "block", "oildrum.json")
    write_json(path, data)
