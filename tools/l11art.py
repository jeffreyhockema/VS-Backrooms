"""Models for the Level 11 props of the "l11art" round (textures: l11art_tex.py).

    hydrant()           a cast-iron hydrant: flange and bolts, barrel, bonnet and dome, a brass operating nut, two side
                        nozzles and a steamer nozzle with capped ends and chains
    postbox()           the street-corner mailbox: legs, plinth, stepped dome, the slot and its hood, a name plate, a
                        pull-down door with a hinge, a handle and a times plate
    mailbox()           the suburban mailbox: a post and bracket, an arched box, a door with latch, the flag
    phonebooth()        a booth: frame posts and mullions, glass panes, kick panels, a lit sign on three sides, a roof, and
                        inside a payphone (keypad, coin slot, handset on its cradle) over a directory shelf
    medcabinet()        a white enamel cabinet: a face frame, four doors with raised panels, hinges, bar pulls and a red cross
    grandpiano()        a grand piano with the lid up on its prop: a stepped bent side, rim, harp plate, keyboard with black
                        keys, music desk, three legs, pedal lyre, and a padded bench
    pantryshelf()       pine shelving with uprights, boards, a beadboard back and stocked tins, jars, sacks and cartons
    directory()         the lobby's directory board: a walnut frame, felt, a brass title plate and three rows of letters
    basement_door(up)   the steel basement door as geometry (four-sided: no facing), with its hardware

Props are modelled with their front to the north (low z). Doors have no facing, so they are built for the north face and
turned four times; the hardware stops short of the block's planes (the graphics pass's B8 lesson).
"""
import math
import random

import modelkit as MK
from deepprops import POST, RECESS, door_core, door_frame, turned
from gen_shapes import octagon

B = MK.box
PX = MK.PX
ALL4 = ("north", "east", "south", "west")
SIDE5 = ALL4 + ("up",)


def tube(name, axis, p0, p1, a, c1, c2, tex, faces=None):
    """A round-ish (octagonal) tube along `axis` ("x" or "z") from p0 to p1 of apothem `a`, its centre line through
    (y = c1, z = c2) for x tubes or (x = c1, y = c2) for z tubes. Two crossed boxes and the same two turned 45 degrees;
    each end sits a hair apart so the overlapping end caps do not share a plane."""
    w = a * math.tan(math.radians(22.5))
    out = []
    for i, (h1, h2, r) in enumerate(((a, w, 0), (w, a, 0), (a, w, 45), (w, a, 45))):
        e = 0.01 * i
        if axis == "x":
            fr, to = (p0, c1 - h1, c2 - h2), (p1 + e, c1 + h1, c2 + h2)
            fcs = faces or ("north", "south", "up", "down", "east", "west")
            out.append(B(f"{name}{i}", fr, to, tex, faces=fcs, rot=(r, 0, 0) if r else None, origin=(p0, c1, c2)))
        else:
            fr, to = (c1 - h2, c2 - h1, p0), (c1 + h2, c2 + h1, p1 + e)
            fcs = faces or ("north", "south", "up", "down", "east", "west")
            out.append(B(f"{name}{i}", fr, to, tex, faces=fcs, rot=(0, 0, r) if r else None, origin=(c1, c2, p0)))
    return out


def flip_x(els):
    """The same parts mirrored left to right about the block's middle (rotations about x stay as they are)."""
    out = []
    for e in els:
        e = {**e}
        (x1, y1, z1), (x2, y2, z2) = e["from"], e["to"]
        e["from"], e["to"] = [round(16 - x2, 4), y1, z1], [round(16 - x1, 4), y2, z2]
        f = e["faces"]
        e["faces"] = {k: v for k, v in {"east": f.get("west"), "west": f.get("east"), "north": f.get("north"), "south": f.get("south"),
                                        "up": f.get("up"), "down": f.get("down")}.items() if v is not None}
        if "rotationOrigin" in e:
            o = e["rotationOrigin"]
            e["rotationOrigin"] = [round(16 - o[0], 4), o[1], o[2]]
            if "rotationZ" in e:
                e["rotationZ"] = -e["rotationZ"]
        out.append(e)
    return out


def frame_ring(name, x1, y1, x2, y2, z1, z2, w, tex, outer=("north", "up", "down", "east", "west")):
    """A rectangular ring of four members of width w round (x1, y1)-(x2, y2), the top and bottom ones the full width."""
    return [B(name + "T", (x1, y2 - w, z1), (x2, y2, z2), tex, faces=("north", "up", "east", "west")),
            B(name + "B", (x1, y1, z1), (x2, y1 + w, z2), tex, faces=("north", "down", "east", "west")),
            B(name + "L", (x1, y1 + w, z1), (x1 + w, y2 - w, z2), tex, faces=("north", "west")),
            B(name + "R", (x2 - w, y1 + w, z1), (x2, y2 - w, z2), tex, faces=("north", "east"))]


# ======================= Fire hydrant =======================

def hydrant():
    R, I, CH, BR = "l11a-hydrant", "l11a-hydrantiron", "l11a-chain", "l11a-brass"
    cx = cz = 8.0
    els = octagon("Flange", cx, cz, 3.5, 0, 1.2, R, faces=SIDE5, lift=0.01)
    for i, (x, z) in enumerate(((cx + 3.0, cz), (cx - 3.0, cz), (cx, cz + 3.0), (cx, cz - 3.0))):
        els.append(B(f"Bolt{i}", (x - 0.4, 1.2, z - 0.4), (x + 0.4, 1.8, z + 0.4), I, faces=SIDE5))
    els += octagon("Barrel", cx, cz, 2.5, 1.2, 7.8, R, faces=ALL4, lift=0.01)
    els += octagon("Waist", cx, cz, 2.85, 3.0, 3.8, R, faces=ALL4 + ("up", "down"), lift=0.01)
    els += octagon("Collar", cx, cz, 3.0, 7.8, 8.8, R, faces=ALL4 + ("up", "down"), lift=0.01)
    for i, (x, z) in enumerate(((cx + 2.7, cz), (cx - 2.7, cz), (cx, cz + 2.7), (cx, cz - 2.7))):
        els.append(B(f"CollarBolt{i}", (x - 0.3, 8.8, z - 0.3), (x + 0.3, 9.3, z + 0.3), I, faces=SIDE5))
    els += octagon("Bonnet", cx, cz, 2.4, 8.8, 10.4, R, faces=ALL4, lift=0.01)
    els += octagon("Dome", cx, cz, 1.9, 10.4, 11.2, R, faces=ALL4 + ("up",), lift=0.01)
    els += octagon("Crown", cx, cz, 1.1, 11.2, 11.8, R, faces=ALL4 + ("up",), lift=0.01)
    els += octagon("Nut", cx, cz, 0.7, 11.8, 12.9, BR, faces=ALL4 + ("up",), lift=0.01)

    def link_run(prefix, pts):
        out = []
        for i, (x, y, z) in enumerate(pts):
            if i % 2 == 0:
                out.append(B(f"{prefix}{i}", (x - 0.4, y - 0.4, z - 0.2), (x + 0.4, y + 0.4, z + 0.2), CH, faces=SIDE5 + ("down",)))
            else:
                out.append(B(f"{prefix}{i}", (x - 0.2, y - 0.4, z - 0.4), (x + 0.2, y + 0.4, z + 0.4), CH, faces=SIDE5 + ("down",)))
        return out

    east = tube("SideBoss", "x", 10.2, 11.0, 1.6, 5.2, cz, R)
    east += tube("SideNozzle", "x", 11.0, 12.3, 1.2, 5.2, cz, I)
    east += tube("SideCap", "x", 12.3, 13.4, 1.5, 5.2, cz, I)
    east += [B("SideCapNut", (13.4, 4.6, cz - 0.6), (13.9, 5.8, cz + 0.6), I, faces=("north", "south", "up", "down", "east")),
             B("SideEye", (12.6, 3.5, cz - 0.3), (13.0, 3.9, cz + 0.3), CH, faces=ALL4 + ("up", "down"))]
    east += link_run("SideLink", [(12.8, 3.1, cz), (12.4, 2.6, cz), (11.9, 2.4, cz), (11.4, 2.5, cz), (10.9, 2.7, cz)])
    els += east + flip_x(east)
    # the steamer nozzle, to the north: a boss, a barrel, a ribbed cap with its nut, a chain
    els += tube("SteamBoss", "z", 5.3, 5.9, 2.2, cx, 4.4, R)
    els += tube("SteamNozzle", "z", 3.7, 5.3, 1.8, cx, 4.4, I)
    els += tube("SteamCap", "z", 2.4, 3.7, 2.1, cx, 4.4, I)
    els += tube("SteamRib", "z", 3.1, 3.4, 2.3, cx, 4.4, I)
    els.append(B("SteamNut", (cx - 0.7, 3.8, 1.9), (cx + 0.7, 5.0, 2.4), I, faces=ALL4 + ("up", "down", "north")))
    els.append(B("SteamEye", (cx + 1.6, 2.4, 3.0), (cx + 2.0, 2.8, 3.4), CH, faces=ALL4 + ("up", "down")))
    els += link_run("SteamLink", [(cx + 1.9, 2.1, 3.7), (cx + 1.9, 1.7, 4.2), (cx + 1.8, 1.8, 4.8), (cx + 1.6, 2.2, 5.3)])
    return els


# ======================= Mailboxes =======================

def postbox():
    S, F, DK, BR, ST = "l11a-postblue", "l11a-postfront", "l11a-darksteel", "l11a-brass", "l11a-steel"
    els = [B("Plate", (3.0, 2.0, 4.0), (13.0, 2.8, 12.0), DK, faces=ALL4 + ("down",))]
    for i, (x, z) in enumerate(((3.6, 4.6), (11.0, 4.6), (3.6, 10.0), (11.0, 10.0))):
        els.append(B(f"Leg{i}", (x, 0, z), (x + 1.4, 2.0, z + 1.4), DK, faces=ALL4 + ("down",)))
    els.append(B("Plinth", (2.6, 2.8, 3.6), (13.4, 3.6, 12.4), S, faces=ALL4 + ("up",)))
    els.append(B("Body", (3.0, 3.6, 4.0), (13.0, 16.6, 12.0), S, faces=("east", "south", "west")))
    els.append(B("Front", (3.0, 3.6, 3.9), (13.0, 16.6, 4.0), F, faces=("north",), uv=[0, 0, 10, 13]))
    els.append(B("Cornice", (2.6, 16.6, 3.6), (13.4, 17.2, 12.4), S, faces=ALL4 + ("up", "down")))
    for i, (x1, x2, y1, y2) in enumerate(((3.4, 12.6, 17.2, 18.2), (4.4, 11.6, 18.2, 19.2), (5.6, 10.4, 19.2, 20.0), (6.8, 9.2, 20.0, 20.6))):
        els.append(B(f"Dome{i}", (x1, y1, 3.8), (x2, y2, 12.2), S, faces=ALL4 + ("up",)))
    els.append(B("Finial", (7.4, 20.6, 7.4), (8.6, 21.0, 8.6), BR, faces=SIDE5))
    # the slot: a housing, the black opening, a hood over it on a lip
    els += [B("SlotHousing", (4.2, 13.0, 3.5), (11.8, 15.4, 3.9), S, faces=("north", "east", "west", "down")),
            B("Slot", (5.2, 13.8, 3.4), (10.8, 14.8, 3.5), "l11a-postslot", faces=("north",)),
            B("HoodLip", (4.6, 15.4, 3.2), (11.4, 15.9, 3.9), S, faces=("north", "east", "west", "down")),
            B("Hood", (4.0, 15.9, 2.8), (12.0, 16.5, 3.9), S, faces=("north", "east", "west", "up", "down"))]
    # a name plate, then the pull-down door on a hinge, its handle and a times plate
    els += [B("NameRim", (3.8, 9.9, 3.5), (12.2, 12.9, 3.9), S, faces=("north", "east", "west", "up", "down")),
            B("Name", (4.0, 10.1, 3.3), (12.0, 12.7, 3.5), "l11a-postname", faces=("north",), uv=[0, 0, 8, 2.6])]
    els += [B("DoorRim", (4.0, 4.2, 3.5), (12.0, 9.6, 3.9), S, faces=("north", "east", "west", "down", "up")),
            B("Door", (4.5, 4.7, 3.2), (11.5, 9.1, 3.5), S, faces=("north", "east", "west", "up", "down")),
            B("Hinge", (4.2, 4.0, 2.9), (11.8, 4.6, 3.4), DK, faces=ALL4 + ("up", "down")),
            B("TimesPlate", (5.6, 6.8, 3.1), (10.4, 8.6, 3.2), "l11a-postplate", faces=("north",), uv=[0, 0, 4.8, 1.8])]
    els += MK.handle("Pull", 8.0, 5.7, 3.2, length=4.4, axis="x", standoff=0.5, thick=0.6, tex=ST)
    els.append(B("LockPlate", (9.6, 8.7, 3.0), (10.8, 9.5, 3.2), BR, faces=("north", "up", "east", "west")))
    return els


def mailbox():
    BX, FL, PST, ST = "l11a-mailbox", "l11a-flag", "l11a-post", "l11a-steel"
    els = [B("Post", (7.0, 0, 7.0), (9.0, 12.2, 9.0), PST, faces=SIDE5 + ("down",)),
           B("PostCap", (6.7, 12.2, 6.7), (9.3, 12.6, 9.3), PST, faces=SIDE5),
           B("Arm", (7.25, 10.0, 5.2), (8.75, 11.2, 12.4), PST, faces=("north", "east", "west", "up", "down")),
           B("Brace", (7.25, 9.2, 5.6), (8.75, 10.0, 9.8), PST, faces=("east", "west", "up", "down"), rot=(-35, 0, 0), origin=(8, 9.6, 5.6)),
           B("Seat", (4.6, 12.6, 3.9), (11.4, 12.9, 13.3), "l11a-darksteel", faces=SIDE5 + ("down",))]
    # the box: a body, then the arch as three steps; the door in front
    els += [B("Body", (5.0, 12.9, 4.0), (11.0, 15.0, 13.0), BX, faces=("east", "south", "west", "down")),
            B("Arch1", (5.0, 15.0, 4.0), (11.0, 16.0, 13.0), BX, faces=("east", "south", "west", "up")),
            B("Arch2", (5.7, 16.0, 4.0), (10.3, 16.9, 13.0), BX, faces=("east", "south", "west", "up")),
            B("Arch3", (6.9, 16.9, 4.0), (9.1, 17.5, 13.0), BX, faces=("east", "south", "west", "up"))]
    els += [B("DoorLow", (5.0, 12.9, 3.6), (11.0, 15.0, 4.0), BX, faces=("north", "east", "west", "down")),
            B("DoorA1", (5.0, 15.0, 3.6), (11.0, 16.0, 4.0), BX, faces=("north", "east", "west", "up")),
            B("DoorA2", (5.7, 16.0, 3.6), (10.3, 16.9, 4.0), BX, faces=("north", "east", "west", "up")),
            B("DoorA3", (6.9, 16.9, 3.6), (9.1, 17.5, 4.0), BX, faces=("north", "east", "west", "up")),
            B("Hinge", (5.05, 12.7, 3.3), (10.95, 13.1, 3.8), ST, faces=("north", "east", "west", "down", "up")),
            B("Latch", (7.3, 15.8, 3.1), (8.7, 16.5, 3.6), ST, faces=("north", "east", "west", "up", "down")),
            B("Number", (5.6, 13.6, 3.5), (7.6, 14.6, 3.6), "l11a-postplate", faces=("north",), uv=[0, 0, 2, 1])]
    # the flag on a pivot on the right-hand side
    els += [B("Pivot", (11.0, 14.0, 8.8), (11.6, 14.8, 9.6), ST, faces=ALL4 + ("up", "down", "east")),
            B("FlagArm", (11.6, 14.0, 8.9), (12.1, 19.0, 9.5), FL, faces=ALL4 + ("up", "east")),
            B("FlagTip", (11.6, 17.6, 9.5), (12.1, 19.0, 11.4), FL, faces=ALL4 + ("up", "east", "down"))]
    return els


# ======================= Phone booth =======================

def phonebooth():
    FR, BK, GL, FL, DK = "l11a-boothframe", "l11a-boothback", "l11a-boothglass", "l11a-boothfloor", "l11a-darksteel"
    els = [B("Base", (1, 0, 1), (15, 1.6, 15), DK, faces=ALL4 + ("down",)),
           B("Floor", (1.6, 1.6, 1.6), (14.4, 2.0, 14.4), FL, faces=("up",))]
    for i, (x, z) in enumerate(((1, 1), (13.6, 1), (1, 13.6), (13.6, 13.6))):
        els.append(B(f"Post{i}", (x, 1.6, z), (x + 1.4, 30, z + 1.4), FR, faces=ALL4))
    # the sides: a kick panel, two rows of panes split by a mullion, rails
    for side, (xa, xb) in (("W", (1.0, 2.4)), ("E", (13.6, 15.0))):
        gx1, gx2 = (1.5, 1.9) if side == "W" else (14.1, 14.5)
        out = ("west",) if side == "W" else ("east",)
        els.append(B(f"Kick{side}", (xa, 1.6, 2.4), (xb, 6.0, 13.6), FR, faces=("north", "south") + out))
        for j, (ya, yb) in enumerate(((6.8, 15.4), (16.4, 28.4))):
            for k, (za, zb) in enumerate(((2.4, 7.3), (8.7, 13.6))):
                els.append(B(f"Pane{side}{j}{k}", (gx1, ya, za), (gx2, yb, zb), GL, faces=("east", "west")))
        els.append(B(f"Sill{side}", (xa, 6.0, 2.4), (xb, 6.8, 13.6), FR, faces=("north", "south", "up", "down") + out))
        els.append(B(f"Rail{side}", (xa, 15.4, 2.4), (xb, 16.4, 13.6), FR, faces=("north", "south", "up", "down") + out))
        els.append(B(f"Head{side}", (xa, 28.4, 2.4), (xb, 30.0, 13.6), FR, faces=("north", "south", "up", "down") + out))
        els.append(B(f"Mull{side}", (xa, 6.8, 7.3), (xb, 28.4, 8.7), FR, faces=("north", "south") + out))
    # the front is open: a head rail and a threshold; the back is a steel panel
    els.append(B("FrontHead", (2.4, 28.4, 1.0), (13.6, 30.0, 2.4), FR, faces=("north", "south", "up", "down")))
    els.append(B("Threshold", (2.4, 2.0, 1.0), (13.6, 2.6, 2.6), DK, faces=("north", "up", "east", "west")))
    els.append(B("Back", (2.4, 2.0, 13.6), (13.6, 28.4, 14.7), BK, faces=("north", "east", "west", "up")))
    els.append(B("BackOut", (2.4, 2.0, 14.7), (13.6, 28.4, 14.9), FR, faces=("south",)))
    # the header box with a lit sign panel on three sides, then the roof
    els.append(B("Header", (1.0, 30.0, 1.0), (15.0, 34.0, 15.0), FR, faces=("north", "south", "east", "west", "up", "down")))
    els.append(B("SignN", (2.0, 30.2, 0.9), (14.0, 33.8, 1.0), "l11a-boothsign", faces=("north",), uv=[0, 0, 16, 16]))
    els.append(B("SignW", (0.9, 30.2, 2.0), (1.0, 33.8, 14.0), "l11a-boothsign", faces=("west",), uv=[0, 0, 16, 16]))
    els.append(B("SignE", (15.0, 30.2, 2.0), (15.1, 33.8, 14.0), "l11a-boothsign", faces=("east",), uv=[0, 0, 16, 16]))
    els += [B("Eave", (0.5, 34.0, 0.5), (15.5, 34.9, 15.5), DK, faces=ALL4 + ("up", "down")),
            B("Crown", (2.0, 34.9, 2.0), (14.0, 35.6, 14.0), FR, faces=ALL4 + ("up",)),
            B("Ridge", (5.0, 35.6, 5.0), (11.0, 36.0, 11.0), FR, faces=ALL4 + ("up",))]
    # the payphone on the back panel: housing, hood, faceplate, coin slot, keypad, handset on its cradle
    els += [B("Housing", (6.2, 12.0, 11.8), (11.2, 21.0, 13.6), "l11a-phonehousing", faces=ALL4 + ("up", "down")),
            B("Hood", (5.9, 21.0, 11.5), (11.5, 22.0, 13.6), "l11a-phonehousing", faces=ALL4 + ("up",)),
            B("FacePlate", (6.5, 12.4, 11.6), (10.9, 20.6, 11.8), "l11a-keyplate", faces=("north", "east", "west", "up", "down")),
            B("CoinSlot", (8.0, 18.6, 11.45), (9.4, 19.4, 11.6), "l11a-postslot", faces=("north",)),
            B("CoinPlate", (7.6, 18.2, 11.5), (9.8, 19.8, 11.6), DK, faces=("north", "east", "west", "up", "down")),
            B("Return", (7.9, 12.8, 11.4), (9.5, 13.8, 11.6), DK, faces=("north", "east", "west", "up", "down"))]
    els += MK.keypad("Keys", 7.1, 14.2, 11.6, cols=3, rows=4, key=0.8, gap=0.3, border=0.4, plate="l11a-darksteel", keys="l11a-key")
    # handset: a handle, an ear piece and a mouth piece, on a hook; a steel cord down to the housing
    els += [B("Handle", (4.9, 14.6, 11.7), (5.9, 20.0, 12.6), "l11a-handset", faces=ALL4 + ("up", "down")),
            B("Ear", (4.4, 19.2, 11.3), (6.4, 20.8, 12.9), "l11a-handset", faces=ALL4 + ("up", "down")),
            B("Mouth", (4.4, 13.6, 11.3), (6.4, 15.2, 12.9), "l11a-handset", faces=ALL4 + ("up", "down")),
            B("Hook", (5.9, 17.0, 12.0), (6.2, 17.6, 12.5), "l11a-steel", faces=ALL4 + ("up", "down")),
            B("Cord1", (5.2, 12.8, 12.1), (5.6, 13.6, 12.5), "l11a-steel", faces=ALL4 + ("down",)),
            B("Cord2", (5.2, 12.4, 12.1), (6.4, 12.8, 12.5), "l11a-steel", faces=ALL4 + ("up", "down"))]
    # the directory shelf below it, a pair of books on it, and the chain
    els += [B("Shelf", (3.4, 8.4, 9.6), (12.6, 9.2, 13.6), "l11a-steel", faces=("north", "east", "west", "up", "down")),
            B("ShelfLip", (3.4, 9.2, 9.6), (12.6, 9.8, 10.0), "l11a-steel", faces=("north", "east", "west", "up")),
            B("BracketL", (3.8, 6.8, 13.2), (4.4, 8.4, 13.6), DK, faces=("north", "east", "west")),
            B("BracketR", (11.6, 6.8, 13.2), (12.2, 8.4, 13.6), DK, faces=("north", "east", "west")),
            B("Book1", (4.2, 9.2, 10.6), (7.8, 15.0, 13.0), "l11a-pages", faces=("north", "up", "east", "south")),
            B("Cover1", (4.2, 9.2, 10.2), (7.8, 15.2, 10.6), "l11a-book", faces=("north", "east", "west", "up", "south"), uv=[0, 0, 3.6, 6]),
            B("Book2", (8.2, 9.2, 11.4), (11.4, 13.6, 13.0), "l11a-pages", faces=("north", "up", "east", "west", "south")),
            B("Cover2", (8.2, 9.2, 11.0), (11.4, 13.8, 11.4), "l11a-book", faces=("north", "east", "west", "up", "south"), uv=[0, 0, 3.2, 4.6])]
    for i, y in enumerate((15.4, 14.8, 14.2)):
        els.append(B(f"Chain{i}", (11.9 + (0.05 if i % 2 else 0), y, 11.3), (12.4 - (0.05 if i % 2 else 0), y + 0.5, 11.7), "l11a-chain", faces=ALL4 + ("up", "down")))
    return els


# ======================= Medical cabinet =======================

def medcabinet():
    EN, EP, FR, RC, ST, DK = "l11a-enamel", "l11a-enameldoor", "l11a-medframe", "l11a-redcross", "l11a-steel", "l11a-darksteel"
    els = []
    for i, (x, z) in enumerate(((2.4, 6.6), (12.6, 6.6), (2.4, 13.4), (12.6, 13.4))):
        els.append(B(f"Foot{i}", (x, 0, z), (x + 1.0, 1.6, z + 1.0), DK, faces=ALL4))
    els.append(B("Carcass", (2.0, 1.6, 6.0), (14.0, 23.2, 15.0), EN, faces=("east", "south", "west", "down")))
    els.append(B("Face", (2.0, 1.6, 5.7), (14.0, 23.2, 6.0), FR, faces=("north",)))
    els.append(B("Top", (1.6, 23.2, 5.6), (14.4, 24.0, 15.0), EN, faces=("north", "east", "south", "west", "up")))
    doors = []
    for tier, (y1, y2) in enumerate(((2.2, 9.8), (10.4, 17.6))):
        for side, (x1, x2) in enumerate(((2.4, 7.85), (8.15, 13.6))):
            tag = f"D{tier}{side}"
            els.append(B(tag, (x1, y1, 5.3), (x2, y2, 5.7), EP, faces=("north", "east", "west", "up", "down")))
            els.append(B(tag + "Panel", (x1 + 0.9, y1 + 0.9, 5.15), (x2 - 0.9, y2 - 0.9, 5.3), EP, faces=("north", "east", "west", "up", "down")))
            doors.append((tag, x1, x2, y1, y2, side))
    for tag, x1, x2, y1, y2, side in doors:
        hx = 13.6 if side else 2.4  # the outer edge: hinges
        for k, hy in enumerate((y1 + 1.2, y2 - 3.2)):
            els.append(B(f"{tag}Hinge{k}", (hx - (0.0 if side == 0 else 0.5), hy, 5.0), (hx + (0.5 if side == 0 else 0.0), hy + 2.0, 5.3), ST,
                         faces=("north", "east", "west", "up", "down")))
        px = 7.2 if side == 0 else 8.8  # the pulls on the meeting edges
        els += MK.handle(f"{tag}Pull", px, (y1 + y2) / 2, 5.3, length=3.2, axis="y", standoff=0.7, thick=0.6, tex=ST)
    # the header: a raised panel carrying a white plate and the red cross
    els.append(B("Header", (2.4, 18.2, 5.3), (13.6, 22.8, 5.7), EP, faces=("north", "east", "west", "up", "down")))
    els.append(B("HeaderPanel", (3.2, 18.8, 5.15), (12.8, 22.2, 5.3), EP, faces=("north", "east", "west", "up", "down")))
    els.append(B("CrossPlate", (5.8, 18.9, 5.0), (10.2, 22.1, 5.15), "l11a-enamelplate", faces=("north", "east", "west", "up", "down")))
    els.append(B("CrossV", (7.2, 19.1, 4.8), (8.8, 21.9, 5.0), RC, faces=("north", "east", "west", "up", "down")))
    els.append(B("CrossH", (6.0, 19.9, 4.8), (10.0, 21.1, 5.0), RC, faces=("north", "east", "west", "up", "down")))
    # a lock on the right-hand lower door
    els.append(B("Lock", (9.7, 5.4, 5.0), (10.7, 6.4, 5.15), "l11a-brass", faces=("north", "east", "west", "up", "down")))
    return els


# ======================= Grand piano =======================

def grandpiano():
    L, LH, EB, BR = "l11a-lacquer", "l11a-lacquerhi", "l11a-ebony", "l11a-brass"
    els = []
    bands = [(1, 12, 0.0, 16.0), (12, 16, 0.8, 16.0), (16, 20, 2.4, 16.0), (20, 24, 4.6, 16.0), (24, 28, 7.4, 14.6)]
    for i, (z0, z1, xa, xb) in enumerate(bands):
        els.append(B(f"Case{i}", (xa, 9.0, z0), (xb, 12.2, z1), LH, faces=("east", "west", "south", "down") + (("north",) if i == 0 else ())))
        els.append(B(f"Board{i}", (xa + 1.0, 12.1, z0), (xb - 1.0, 12.3, z1), "l11a-sound", faces=("up",)))
        # the rim: the bent side and the straight side
        els.append(B(f"RimW{i}", (xa, 12.2, z0), (xa + 1.0, 13.0 + 0.01 * i, z1), L, faces=("north", "south", "east", "west", "up")))
        els.append(B(f"RimE{i}", (xb - 1.0, 12.2, z0), (xb, 13.0 + 0.01 * i, z1), L, faces=("north", "south", "east", "west", "up")))
    els.append(B("RimTail", (7.4, 12.2, 27.0), (14.6, 13.0, 28.0), L, faces=("north", "south", "east", "west", "up")))
    for i in range(1, len(bands)):  # the steps of the bent side are closed by a riser across
        z0, xa_prev, xa = bands[i][0], bands[i - 1][2], bands[i][2]
        els.append(B(f"Riser{i}", (xa_prev, 12.2, z0 - 1.0), (xa + 1.0, 13.0 + 0.02 * i, z0), L, faces=("north", "south", "up")))
    els.append(B("RiserE", (13.6, 12.2, 23.0), (16.0, 13.04, 24.0), L, faces=("north", "south", "up", "east")))
    # the harp: the gold plate over the soundboard, strings running back to front
    els.append(B("Harp", (1.4, 12.3, 3.0), (14.6, 12.6, 16.6), "l11a-plate", faces=("up", "north", "east", "west", "south")))
    els.append(B("HarpTail", (8.6, 12.3, 16.6), (13.4, 12.6, 26.4), "l11a-plate", faces=("up", "east", "west", "south")))
    # the nameboard and a brass name
    els.append(B("Nameboard", (1.0, 12.2, 1.0), (15.0, 14.6, 1.9), L, faces=("north", "east", "west", "up")))
    els.append(B("NameBrass", (6.4, 13.2, 0.8), (9.6, 13.7, 1.0), BR, faces=("north",)))
    # the keyboard: cheeks, a key bed, white keys, black keys
    els += [B("CheekW", (0.0, 9.0, -3.0), (1.4, 12.2, 1.0), LH, faces=("north", "east", "west", "up", "down")),
            B("CheekE", (14.6, 9.0, -3.0), (16.0, 12.2, 1.0), LH, faces=("north", "east", "west", "up", "down")),
            B("KeyBed", (1.4, 9.0, -3.0), (14.6, 10.4, 1.0), L, faces=("north", "down")),
            B("KeysTop", (1.4, 10.4, -3.0), (14.6, 11.4, 1.0), "l11a-keys", faces=("up",), uv=[0, 0, 13.2, 4]),
            B("KeysFront", (1.4, 10.4, -3.1), (14.6, 11.4, -3.0), "l11a-keyfront", faces=("north",), uv=[0, 0, 13.2, 1]),
            B("KeySlip", (1.4, 11.4, 0.4), (14.6, 12.2, 1.0), L, faces=("north", "up"))]
    for j in (0, 1, 3, 4, 5, 7, 8, 10, 11):
        cx = 1.4 + (j + 1) - 0.25
        els.append(B(f"Black{j}", (cx - 0.35, 11.4, -1.2), (cx + 0.35, 12.0, 0.4), EB, faces=("north", "east", "west", "up")))
    # the lid, raised on its prop: hinged along the straight side
    pivot = (16.0, 13.4, 0)
    lid = [B("LidA", (0.0, 13.0, 2.0), (16.0, 13.8, 20.0), LH, faces=("north", "south", "east", "west", "up", "down"), rot=(0, 0, -24), origin=pivot),
           B("LidB", (4.6, 13.0, 20.0), (16.0, 13.8, 24.0), LH, faces=("south", "east", "west", "up", "down"), rot=(0, 0, -24), origin=pivot),
           B("LidC", (7.4, 13.0, 24.0), (14.6, 13.8, 28.0), LH, faces=("north", "south", "east", "west", "up", "down"), rot=(0, 0, -24), origin=pivot)]
    els += lid
    els.append(B("Hinge", (15.4, 13.0, 3.0), (16.4, 14.0, 26.0), BR, faces=("east", "up", "north", "south")))
    els.append(B("Prop", (3.0, 13.0, 12.0), (3.5, 19.2, 12.5), L, faces=ALL4 + ("up",)))
    # the music desk, leaning back on the nameboard
    els += [B("Desk", (2.5, 14.6, 1.0), (13.5, 20.4, 1.4), L, faces=("north", "east", "west", "up"), rot=(-12, 0, 0), origin=(8, 14.6, 1.2)),
            B("DeskLip", (2.5, 14.6, 0.2), (13.5, 15.3, 1.0), L, faces=("north", "east", "west", "up"), rot=(-12, 0, 0), origin=(8, 14.6, 1.2)),
            B("Sheet", (3.4, 15.6, 0.7), (12.6, 19.8, 0.95), "l11a-sheet", faces=("north",), rot=(-12, 0, 0), origin=(8, 14.6, 1.2), uv=[0, 0, 9.2, 4.2])]
    # three legs, each stepped and turned, on brass casters
    for i, (cx, cz) in enumerate(((2.0, 0.2), (14.0, 0.2), (12.8, 25.4))):
        els += [B(f"Leg{i}Top", (cx - 1.3, 6.8, cz - 1.3), (cx + 1.3, 9.0, cz + 1.3), L, faces=ALL4 + ("down",)),
                B(f"Leg{i}Mid", (cx - 0.9, 3.0, cz - 0.9), (cx + 0.9, 6.8, cz + 0.9), L, faces=ALL4),
                B(f"Leg{i}Low", (cx - 0.65, 1.0, cz - 0.65), (cx + 0.65, 3.0, cz + 0.65), L, faces=ALL4 + ("down",)),
                B(f"Leg{i}Caster", (cx - 0.7, 0.0, cz - 0.7), (cx + 0.7, 1.0, cz + 0.7), BR, faces=ALL4 + ("down",))]
    # the pedal lyre
    els += [B("LyreL", (6.6, 2.6, -0.4), (7.2, 9.0, 0.2), L, faces=ALL4),
            B("LyreR", (8.8, 2.6, -0.4), (9.4, 9.0, 0.2), L, faces=ALL4),
            B("LyreBar", (6.6, 5.4, -0.4), (9.4, 5.9, 0.2), L, faces=("north", "up", "down")),
            B("PedalBox", (6.0, 1.4, -0.6), (10.0, 2.6, 1.6), L, faces=("north", "east", "west", "up", "south"))]
    for i, x in enumerate((6.3, 7.5, 8.7)):
        els.append(B(f"Pedal{i}", (x, 0.8, -2.2), (x + 1.0, 1.4, -0.6), BR, faces=("north", "up", "east", "west")))
    # the bench: lacquer legs and rails, a board and a padded seat
    els.append(B("SeatBoard", (3.0, 6.2, -10.8), (13.0, 7.2, -4.4), L, faces=ALL4 + ("down",)))
    els.append(B("Cushion", (3.3, 7.2, -10.5), (12.7, 8.6, -4.7), "l11a-velvet", faces=ALL4 + ("up",)))
    for i, (x, z) in enumerate(((3.4, -10.4), (11.6, -10.4), (3.4, -5.4), (11.6, -5.4))):
        els.append(B(f"BenchLeg{i}", (x, 0, z), (x + 1.0, 6.2, z + 1.0), L, faces=ALL4 + ("down",)))
    els.append(B("RailF", (4.4, 2.6, -10.2), (11.6, 3.2, -9.6), L, faces=("north", "south", "up")))
    els.append(B("RailB", (4.4, 2.6, -5.2), (11.6, 3.2, -4.6), L, faces=("north", "south", "up")))
    return els


# ======================= Pantry shelf =======================

def pantryshelf():
    P, PV, BD = "l11a-pine", "l11a-pinev", "l11a-bead"
    els = [B("UpL", (0.5, 0, 7.5), (1.6, 27.2, 16.0), PV, faces=ALL4 + ("up",)),
           B("UpR", (14.4, 0, 7.5), (15.5, 27.2, 16.0), PV, faces=ALL4 + ("up",)),
           B("Back", (1.6, 2.4, 15.4), (14.4, 27.2, 16.0), BD, faces=("north", "east", "west", "up")),
           B("Plinth", (1.6, 0, 8.2), (14.4, 2.4, 15.4), P, faces=("north", "east", "west")),
           B("Top", (0.5, 27.2, 7.5), (15.5, 28.0, 16.0), P, faces=ALL4 + ("up", "down"))]
    boards = [(2.4, 3.2), (9.6, 10.4), (16.4, 17.2), (22.8, 23.6)]
    for i, (y1, y2) in enumerate(boards):
        els.append(B(f"Board{i}", (1.6, y1, 7.8), (14.4, y2, 15.4), P, faces=("north", "up", "down", "east", "west")))
        els.append(B(f"Lip{i}", (1.6, y2, 7.8), (14.4, y2 + 0.6, 8.3), P, faces=("north", "up", "east", "west")))
    rng = random.Random(1111)

    def can(name, cx, cz, y, tex, r=1.2, h=3.6):
        out = octagon(name, cx, cz, r, y, y + h, tex, faces=ALL4, lift=0.01)
        out.append(B(name + "Lid", (cx - r * 0.82, y + h, cz - r * 0.82), (cx + r * 0.82, y + h + 0.1, cz + r * 0.82), "l11a-tinlid", faces=("up",)))
        return out

    def jar(name, cx, cz, y, tex, r=1.5, h=4.4):
        out = octagon(name, cx, cz, r, y, y + h, tex, faces=ALL4, lift=0.01)
        out.append(B(name + "Lid", (cx - r * 0.85, y + h, cz - r * 0.85), (cx + r * 0.85, y + h + 0.7, cz + r * 0.85), "l11a-jarlid", faces=SIDE5))
        return out

    # shelf 0 (3.2): flour sacks and a big tin
    y = 3.2
    els += [B("Sack0", (2.4, y, 8.8), (7.4, y + 5.2, 13.4), "l11a-sack", faces=("east", "south", "west", "up")),
            B("Sack0F", (2.4, y, 8.7), (7.4, y + 5.2, 8.8), "l11a-sackfront", faces=("north",), uv=[0, 0, 5, 5.2]),
            B("SackTie0", (4.0, y + 5.2, 10.4), (5.8, y + 5.9, 11.8), "l11a-sacktie", faces=SIDE5),
            B("Sack1", (7.9, y, 9.4), (12.4, y + 4.4, 13.8), "l11a-sack", faces=("east", "south", "west", "up")),
            B("Sack1F", (7.9, y, 9.3), (12.4, y + 4.4, 9.4), "l11a-sackfront", faces=("north",), uv=[0, 0, 4.5, 4.4])]
    els += can("BigTin", 13.4, 10.6, y, "l11a-tintomato", r=1.0, h=2.8)
    # shelf 1 (10.4): jars and a bottle of oil
    y = 10.4
    for i, (cx, tex) in enumerate(((3.8, "l11a-jarjam"), (7.0, "l11a-jarpickle"), (10.2, "l11a-jarhoney"))):
        els += jar(f"Jar{i}", cx, 10.4 + rng.uniform(-0.4, 0.4), y, tex)
    els += octagon("Oil", 13.0, 11.0, 1.0, y, y + 4.6, "l11a-oil", faces=ALL4, lift=0.01)
    els.append(B("OilNeck", (12.6, y + 4.6, 10.6), (13.4, y + 5.6, 11.4), "l11a-oil", faces=SIDE5))
    els.append(B("OilCork", (12.7, y + 5.6, 10.7), (13.3, y + 6.0, 11.3), "l11a-sacktie", faces=SIDE5))
    # shelf 2 (17.2): a row of cans (one stacked), a cereal carton
    y = 17.2
    for i, (cx, tex) in enumerate(((3.2, "l11a-tintomato"), (5.8, "l11a-tinbeans"), (8.4, "l11a-tinpeas"))):
        els += can(f"Can{i}", cx, 9.8 + 0.5 * (i % 2), y, tex)
    els += can("CanStack", 5.8, 9.8, y + 3.7, "l11a-tintomato")
    els += [B("Carton", (10.2, y, 9.4), (13.4, y + 5.0, 11.4), "l11a-cartonside", faces=("east", "south", "west")),
            B("CartonF", (10.2, y, 9.3), (13.4, y + 5.0, 9.4), "l11a-cereal", faces=("north",), uv=[0, 0, 3.2, 5]),
            B("CartonTop", (10.2, y + 5.0, 9.4), (13.4, y + 5.04, 11.4), "l11a-cartontop", faces=("up",))]
    # shelf 3 (23.6): small tins, a box of tea
    y = 23.6
    for i, cx in enumerate((3.2, 5.4)):
        els += can(f"Tin{i}", cx, 10.0 + 0.4 * i, y, "l11a-tintea", r=0.9, h=2.4)
    els += [B("Tea", (8.0, y, 9.6), (11.0, y + 3.0, 11.2), "l11a-cartonside", faces=("east", "south", "west")),
            B("TeaF", (8.0, y, 9.5), (11.0, y + 3.0, 9.6), "l11a-tea", faces=("north",), uv=[0, 0, 3, 3]),
            B("TeaTop", (8.0, y + 3.0, 9.6), (11.0, y + 3.04, 11.2), "l11a-cartontop", faces=("up",))]
    return els


# ======================= Directory board =======================

def directory():
    """The board on the wall (z 0 is the wall, the front toward -z): a stepped walnut frame, black-blue felt, a brass title
    plate and three rows of letters, each on an aluminium track."""
    W = "l11a-walnut"
    els = frame_ring("FrameA", 1.0, 1.0, 15.0, 15.0, -1.0, 0.0, 1.0, W)
    els += frame_ring("FrameB", 2.0, 2.0, 14.0, 14.0, -0.6, 0.0, 1.0, W)
    els.append(B("Felt", (3.0, 3.0, -0.4), (13.0, 13.0, 0.0), "l11a-felt", faces=("north",), uv=[0, 0, 10, 10]))
    els.append(B("Title", (3.0, 11.0, -0.8), (13.0, 13.0, -0.4), "l11a-dirhead", faces=("north",), uv=[0, 0, 16, 16]))
    els.append(B("TitleSides", (3.0, 11.0, -0.8), (13.0, 13.0, -0.4), "l11a-ledge", faces=("east", "west", "up", "down")))
    for i, y in enumerate((8.4, 5.8, 3.4)):
        els.append(B(f"Track{i}", (3.0, y - 0.3, -0.85), (13.0, y, -0.4), "l11a-ledge", faces=("north", "east", "west", "up", "down")))
        els.append(B(f"Row{i}", (3.0, y, -0.75), (13.0, y + 2.0, -0.4), f"l11a-dirrow{i}", faces=("north",), uv=[0, 0, 16, 16]))
        els.append(B(f"RowSides{i}", (3.0, y, -0.75), (13.0, y + 2.0, -0.4), "l11a-felt", faces=("east", "west", "up")))
    return els


# ======================= Basement door =======================

def basement_door(upper):
    leaf = "l11a-doorleaf-" + ("upper" if upper else "lower")
    els = door_frame(upper, "l11a-doorframe") + door_core(upper, leaf)
    z0 = RECESS - 0.05
    hw = []
    if not upper:
        hw += MK.kick_plate("Kick", 2.5, 13.5, 0.5, 4.5, RECESS, tex="l11a-doorkick", t=0.3)
        hw += MK.bevelled_box("Panel", (2.6, 6.0, RECESS - 0.7), (11.4, 14.4, RECESS - 0.05), {"all": "l11a-doorpanel-lower"}, b=0.25)
        hw += [B("LeverRose", (12.1, 8.1, z0 - 0.4), (13.9, 9.9, z0), "l11a-lever", faces=("north", "up", "down", "east", "west")),
               B("LeverNeck", (12.7, 8.7, z0 - 0.9), (13.3, 9.3, z0 - 0.4), "l11a-lever", faces=("north", "up", "down", "east", "west")),
               B("Lever", (10.0, 8.6, z0 - 1.3), (13.3, 9.4, z0 - 0.9), "l11a-lever", faces=("north", "south", "up", "down", "east", "west"))]
        hw += [B("Escutcheon", (12.2, 11.4, RECESS - 0.5), (13.8, 13.8, RECESS), "l11a-lever", faces=("north", "up", "down", "east", "west")),
               B("Keyhole", (12.7, 12.0, RECESS - 0.58), (13.3, 13.2, RECESS - 0.5), "l11a-postslot", faces=("north",))]
        for i, y in enumerate((3, 8, 13)):
            hw.append(B(f"Hinge{i}", (POST, y, RECESS - 0.35), (POST + 1.6, y + 2, RECESS), "l11a-darksteel", faces=("north", "east", "up", "down")))
    else:
        hw += MK.bevelled_box("Panel", (2.6, 1.0, RECESS - 0.7), (13.4, 7.8, RECESS - 0.05), {"all": "l11a-doorpanel-upper"}, b=0.25)
        hw += [B("SignRim", (1.9, 8.8, RECESS - 0.55), (14.1, 13.2, RECESS - 0.05), "l11a-lever", faces=("north", "up", "down", "east", "west")),
               B("Sign", (2.0, 9.0, RECESS - 0.62), (14.0, 13.0, RECESS - 0.55), "l11a-doorsign", faces=("north",), uv=[0, 0, 16, 16])]
        for i, y in enumerate((3, 7, 11)):
            hw.append(B(f"Hinge{i}", (POST, y, RECESS - 0.35), (POST + 1.6, y + 2, RECESS), "l11a-darksteel", faces=("north", "east", "up", "down")))
    return els + turned(hw)
