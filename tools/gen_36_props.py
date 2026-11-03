"""Level 36 "Airport" (experimental): the level's prop models, their textures (tools/gen_36_props_tex.py) and block types.

    l36-checkin-{part}-{side}       part desk|scale: a check-in counter (warm-grey laminate front, stainless kick plate,
                                    backlit LIMINAL AIR strip, the agent's monitor and boarding-pass printer behind) and
                                    the baggage scale between two counters (tread plate, a belt into a hooded opening,
                                    a weight display on a stalk)
    l36-seat-{kind}-{side}          kind blue|grey|coat|bag: a gate seat on a shared floor beam (navy or charcoal; coat:
                                    a jacket left draped over it; bag: an abandoned backpack on it)
    l36-gatedesk-{side}             the gate podium: chest high, curved, a screen and a gooseneck microphone
    l36-gatedoor-{part}-{side}      part lower|upper: the jet-bridge door in the holdroom wall, a FULL CUBE wall block
                                    (cladding on five faces, the steel door on <side>); structure; BackroomsL36GateDoor
    l36-stanchion-{belt}            belt none|north|east|south|west: a queue post, its navy belt to that edge's middle
    l36-scanner-{part}-{side}       part lower|upper: a walk-through metal detector arch (walk along the <side> axis)
    l36-xray-{part}-{side}          part body|belt: the X-ray baggage machine (1.5 blocks tall) and its roller bed
    l36-trays                       a stack of grey security trays
    l36-booth-{part}-{side}         part desk|rack|signl|signm|signr: the Backrooms Travel Agency booth ("booth 0");
                                    the sign parts hang from the top of their block and glow
    l36-perfume-{side}              a duty-free perfume counter (glass case, tinted bottles, testers)
    l36-mealtable-{kind}            kind tray|cups|plate|clean: a food-court table with what was left on it
    l36-meetingpoint-{part}         part base|mid|top: the Meeting Place column; top lit (light 10)
    l36-cabinseat-{side}            an airline economy seat
    l36-lostfound-{side}            a Lost & Found shelf unit crammed with luggage
    l36-airportdoor-{part}-{side}   (links) part lower|upper: a glazed aluminium door, a FULL CUBE wall block (dark steel on
                                    five faces, the door on <side>): in the baggage wall, and found in walls of Levels 9 and
                                    11; structure; BackroomsThreshold kind l36-airport
    l36-airportsign-{side}          (links) the backlit sign over it: the airplane on a yellow tile, an arrow down; a FULL CUBE
    l36-sink-{state}-{side}         (links) state dry|overflow: a restroom washbasin on its vanity (a white bowl, a chrome tap,
                                    a splashback); overflowing, water to the rim, over it and down the front onto the floor;
                                    structure; BackroomsL36Sink

`side` is the way the front faces; every shape is modelled facing north (front toward -Z) and turned with rotateY as
Level 3999 does (north 0, east 270, south 180, west 90). Seen from the north, the viewer's left is +X.
Run from the worktree root:  bash tools/locked.sh run python tools/gen_36_props.py
"""
import itertools
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import modelkit as MK  # noqa: E402
import gen_36_props_tex as TX  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
SHAPES = os.path.join(ASSETS, "shapes", "block", "36")
BLOCKS = os.path.join(ASSETS, "blocktypes", "36")
TEXPATH = "backrooms:block/36/props/"

SIDES = ["north", "east", "south", "west"]
ROTATE = {"north": 0, "east": 270, "south": 180, "west": 90}
DIRS = MK.DIRS
SIDE4 = ("north", "east", "south", "west")

WOOD = {"walk": "game:walk/wood*", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"}
METAL = {"walk": "game:walk/stone*", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"}
CLOTH = {"walk": "game:walk/cloth", "place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"}
GLASS = {"walk": "game:walk/stone*", "place": "game:block/glass", "break": "game:block/glass", "hit": "game:block/glass"}
CERAMIC = {"walk": "game:walk/stone*", "place": "game:block/ceramicplace", "break": "game:block/ceramicbreak", "hit": "game:block/ceramichit"}
STONE = {"walk": "game:walk/stone*", "place": "game:block/loosestone*", "break": "game:block/rock-break-pickaxe", "hit": "game:block/rock-hit-pickaxe"}

# Display names (lang keys -> English); the lead merges them into en.json
NAMES = {
    "block-l36-checkin-desk-*": "Check-in Counter",
    "block-l36-checkin-scale-*": "Baggage Scale",
    "block-l36-seat-blue-*": "Gate Seat",
    "block-l36-seat-grey-*": "Gate Seat",
    "block-l36-seat-coat-*": "Gate Seat (Jacket Left Behind)",
    "block-l36-seat-bag-*": "Gate Seat (Backpack Left Behind)",
    "block-l36-gatedesk-*": "Gate Podium",
    "block-l36-gatedoor-*": "Jet Bridge Door",
    "block-l36-stanchion-*": "Queue Barrier",
    "block-l36-scanner-*": "Metal Detector Arch",
    "block-l36-xray-body-*": "X-ray Baggage Scanner",
    "block-l36-xray-belt-*": "Roller Conveyor",
    "block-l36-trays": "Security Trays",
    "block-l36-booth-desk-*": "Travel Agency Counter",
    "block-l36-booth-rack-*": "Brochure Rack",
    "block-l36-booth-signl-*": "Travel Agency Sign",
    "block-l36-booth-signm-*": "Travel Agency Sign",
    "block-l36-booth-signr-*": "Travel Agency Sign",
    "block-l36-perfume-*": "Perfume Counter",
    "block-l36-mealtable-*": "Food Court Table",
    "block-l36-meetingpoint-*": "Meeting Place Marker",
    "block-l36-cabinseat-*": "Economy Seat",
    "block-l36-lostfound-*": "Lost and Found Shelf",
    "block-l36-airportdoor-*": "Door Under an Airplane Sign",
    "block-l36-airportsign-*": "Airplane Sign",
    "block-l36-sink-*": "Washbasin",
}

CODES = []
SHAPE_FILES = []


# ======================================================================== Element helpers

def B(name, frm, to, tex, faces=None, glow=0, rot=None, origin=None, uv=None):
    """A box (modelkit.box): tex is one key or a dict by role (top, side, front, back, bottom) or by face."""
    return MK.box(name, frm, to, tex, faces=faces or DIRS, glow=glow, rot=rot, origin=origin, uv=uv)


def no(*drop):
    return tuple(f for f in DIRS if f not in drop)


def pic(el, face, key, glow=0, uv=(0, 0, 16, 16)):
    """Stretches a whole picture texture over one face."""
    el["faces"][face] = {"texture": "#" + key, "uv": list(uv)}
    if glow:
        el["faces"][face]["glow"] = glow
    return el


def glow(els, g):
    for e in els:
        for f in e["faces"].values():
            f["glow"] = g
    return els


def turned(els, rx=0, ry=0, rz=0, origin=(8, 0, 8)):
    """Sets one rotation about `origin` on elements that have none (a part tilted or turned as a whole)."""
    for e in els:
        assert not any(k in e for k in ("rotationX", "rotationY", "rotationZ")), e["name"]
        e["rotationOrigin"] = [round(v, 4) for v in origin]
        for k, a in (("rotationX", rx), ("rotationY", ry), ("rotationZ", rz)):
            if a:
                e[k] = a
    return els


def transparent(el):
    el["renderPass"] = 3
    return el


def octagon(name, cx, cz, r, y1, y2, tex, faces=None, step=0.02):
    """A regular octagonal prism of inradius r: two crossed boxes and the same turned 45 degrees; each box's top and
    bottom a hair apart, so no two faces share a plane."""
    a = r * math.tan(math.pi / 8)
    els = []
    for k, (hx, hz, ry) in enumerate(((r, a, 0), (a, r, 0), (r, a, 45), (a, r, 45))):
        d = k * step
        els.append(B(f"{name}{k}", (cx - hx, y1 + d, cz - hz), (cx + hx, y2 - d, cz + hz), tex, faces=faces,
                     rot=(0, ry, 0) if ry else None, origin=(cx, y1, cz)))
    return els


def mirror_x(els):
    """The elements mirrored left to right (x -> 16 - x), east and west faces swapped, Y/Z rotations negated."""
    out = []
    for e in json.loads(json.dumps(els)):
        (x1, y1, z1), (x2, y2, z2) = e["from"], e["to"]
        e["from"], e["to"] = [16 - x2, y1, z1], [16 - x1, y2, z2]
        f = e["faces"]
        east, west = f.pop("east", None), f.pop("west", None)
        if west is not None:
            f["east"] = west
        if east is not None:
            f["west"] = east
        if "rotationOrigin" in e:
            o = e["rotationOrigin"]
            e["rotationOrigin"] = [16 - o[0], o[1], o[2]]
            for k in ("rotationY", "rotationZ"):
                if k in e:
                    e[k] = -e[k]
        out.append(e)
    return out


# ======================================================================== Files

def write_json(path, data, comment=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(data, indent="\t", ensure_ascii=False)
    if comment:
        text = "// " + comment + "\n" + text
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")


def shape(name, els):
    keys = sorted({f["texture"][1:] for e in els for f in e["faces"].values()})
    names = [e["name"] for e in els]
    assert len(names) == len(set(names)), (name, [n for n in names if names.count(n) > 1])
    write_json(os.path.join(SHAPES, name + ".json"),
               {"textureWidth": 16, "textureHeight": 16, "textures": {k: TEXPATH + k for k in keys}, "elements": els})
    SHAPE_FILES.append(name)
    return "backrooms:block/36/" + name


def cuboid(b, angle=0):
    x1, y1, z1, x2, y2, z2 = b
    c = {"x1": x1, "y1": y1, "z1": z1, "x2": x2, "y2": y2, "z2": z2}
    if angle and not (abs(x1 + x2 - 1) < 1e-9 and abs(z1 + z2 - 1) < 1e-9 and (angle == 180 or abs(x2 - x1 - (z2 - z1)) < 1e-9)):
        c["rotateY"] = angle
    return c


def block(code, groups, build, comment, boxes=None, sel=None, rot="side", material="Wood", sounds=WOOD, data=None):
    """A block type over every combination of `groups` [(group, states)]. build(v) gives a variant's elements, modelled
    facing north; the group named `rot` turns it. boxes / sel are the collision / selection boxes (lists of 6-tuples in
    block units, unturned), or functions of v; None (or a function returning None) means no collision. sel defaults
    to boxes."""
    combos = list(itertools.product(*[s for _, s in groups])) if groups else [()]
    shapes, coll, sels, cache = {}, {}, {}, {}
    for combo in combos:
        v = dict(zip([g for g, _ in groups], combo))
        key = tuple(s for (g, _), s in zip(groups, combo) if g != rot or s not in ROTATE)
        if key not in cache:
            cache[key] = shape(code + ("-" + "-".join(key) if key else ""), build(v))
        full = code + ("-" + "-".join(combo) if combo else "")
        angle = ROTATE.get(v[rot], 0) if rot in v else 0
        shapes[full] = {"base": cache[key], "rotateY": angle} if angle else {"base": cache[key]}
        cb = boxes(v) if callable(boxes) else boxes
        sb = sel(v) if callable(sel) else sel
        if sb is None:
            sb = cb
        coll[full] = [cuboid(b, angle) for b in cb] if cb else None
        sels[full] = [cuboid(b, angle) for b in sb] if sb else None
    out = {"code": code}
    if groups:
        out["variantgroups"] = [{"code": g, "states": list(s)} for g, s in groups]
    if len(shapes) == 1:
        out["shape"] = next(iter(shapes.values()))
    else:
        out["shapeByType"] = shapes
    pattern = ["*-north"] if rot == "side" and rot in [g for g, _ in groups] else ["*"]
    out["creativeinventory"] = {"general": pattern, "backrooms": pattern}
    out.update({"blockmaterial": material, "drawtype": "json", "sidesolid": {"all": False}, "sideopaque": {"all": False},
                "lightAbsorption": 0, "resistance": 2, "sounds": sounds})
    for key, table in (("collisionbox", coll), ("selectionbox", sels)):
        values = list(table.values())
        if all(json.dumps(x) == json.dumps(values[0]) for x in values):
            one = values[0]
            if one is None:
                out[key] = None
            elif len(one) == 1:
                out[key] = one[0]
            else:
                out[key + "es"] = one
        elif any(x is None for x in values) or all(len(x) == 1 for x in values if x):
            assert all(x is None or len(x) == 1 for x in values), (code, key, "None mixed with several boxes")
            out[key + "ByType"] = {k: (x[0] if x else None) for k, x in table.items()}
        else:
            out[key + "esByType"] = table
    out["drops"] = []
    if data:
        out.update(data)
    write_json(os.path.join(BLOCKS, code + ".json"), out, comment)
    CODES.append(code)


# ======================================================================== 1. Check-in counters

LAM = {"front": "laminate", "side": "laminate-side", "top": "laminate-side", "back": "laminate-side", "bottom": "laminate-side"}


def checkin_desk():
    els = [
        # the passengers' side: a warm-grey laminate front on a stainless kick plate, a backlit airline strip
        B("Front", (0.25, 0, 1.25), (15.75, 16.5, 3), LAM, faces=no("down")),
        B("Joint", (0, 0, 1.75), (16, 16.5, 3), "laminate-side", faces=("north", "east", "west")),
        B("Kick", (0.25, 0, 0.75), (15.75, 2.5, 1.25), "steel", faces=("north", "up", "east", "west")),
        pic(B("Logo", (2.5, 11.5, 0.75), (13.5, 13.5, 1.25), "laminate-side", faces=("north", "up", "down", "east", "west")), "north", "logostrip", glow=170),
        B("Reveal", (0.25, 9.5, 1.0), (15.75, 10, 1.25), "laminate-side", faces=("north", "up", "down", "east", "west")),
        # the ledge passengers lean on: a worktop with a stainless front edge
        B("Ledge", (0, 16.5, 0.25), (16, 18, 6), {"top": "worktop", "front": "steel", "side": "steel", "back": "steel", "bottom": "laminate-side"}),
        # the agent's side: a cabinet under the ledge, a worktop, gables and a drawer pedestal
        B("Body", (0, 0, 3), (16, 11, 6), "laminate-side", faces=("south", "east", "west")),
        B("Work", (0, 11, 3), (16, 12, 15.5), {"top": "worktop", "front": "steel", "side": "steel", "back": "steel", "bottom": "laminate-side"}),
        B("GableW", (0, 0, 6), (0.75, 11, 15.5), "laminate-side", faces=no("up", "down")),
        B("GableE", (15.25, 0, 6), (16, 11, 15.5), "laminate-side", faces=no("up", "down")),
        B("Pedestal", (9.5, 0, 6.5), (15.25, 11, 15), "laminate-side", faces=("south", "west")),
    ]
    for i, (y1, y2) in enumerate(((0.75, 5.5), (6, 10.5))):
        els.append(B(f"Drawer{i}", (9.9, y1, 15), (14.85, y2, 15.4), "laminate", faces=no("north")))
        els.append(B(f"Pull{i}", (11.4, y2 - 1.4, 15.4), (13.4, y2 - 0.9, 15.9), "steel", faces=no("north")))
    # the agent's monitor, its screen toward the back (the agent's side), and the boarding-pass printer
    els += [
        B("MonBase", (4.5, 12, 9.5), (8.5, 12.5, 12.5), "darkplastic"),
        B("MonNeck", (6, 12.5, 10.75), (7, 15, 11.5), "darkplastic", faces=no("up", "down")),
        B("Monitor", (2.5, 14, 10.0), (11, 20, 10.75), "darkplastic"),
        pic(B("Screen", (3, 14.5, 10.75), (10.5, 19.5, 11), "black", faces=("south", "east", "west", "up", "down")), "south", "screen", glow=110),
        B("Keyboard", (3.5, 12, 12.75), (9.5, 12.5, 14.75), {"top": "black", "side": "darkplastic"}, faces=no("down")),
        B("Printer", (11.5, 12, 7.5), (15, 14.5, 11), {"top": "lightplastic", "side": "lightplastic", "front": "lightplastic", "back": "lightplastic", "bottom": "lightplastic"}),
        B("PrinterSlot", (12, 13.1, 11), (14.5, 13.6, 11.15), "black", faces=("south",)),
        B("Pass", (12.4, 13.25, 11), (14.1, 13.45, 13), "tag", faces=("up", "down", "south", "east", "west")),
    ]
    return els


def checkin_scale():
    els = [
        # the scale platform at the front, a belt behind running back into a hooded opening (the wall's)
        B("Scale", (1.25, 0, 0.5), (14.75, 2, 7.5), {"top": "tread", "side": "steel"}, faces=no("down")),
        B("Gap", (1.25, 0, 7.5), (14.75, 1.5, 8), "black", faces=("up",)),
        B("Belt", (1.25, 0, 8), (14.75, 2.25, 16), {"top": "beltrubber", "side": "darksteel"}, faces=("up", "north")),
        B("RailW", (0.5, 0, 0.5), (1.25, 3.5, 12.5), "steel", faces=no("down", "south")),
        B("RailE", (14.75, 0, 0.5), (15.5, 3.5, 12.5), "steel", faces=no("down", "south")),
        B("HoodW", (0.5, 0, 12.5), (1.25, 12, 16), "steel", faces=("north", "east", "west", "up")),
        B("HoodE", (14.75, 0, 12.5), (15.5, 12, 16), "steel", faces=("north", "east", "west", "up")),
        B("HoodTop", (0.5, 12, 12.5), (15.5, 12.75, 16), "steel", faces=("north", "up", "down", "east", "west")),
        B("HoodHead", (1.25, 9, 12.5), (14.75, 12, 13), "steel", faces=("north", "down")),
        B("Curtain", (1.25, 2.25, 13.25), (14.75, 9, 13.5), "curtain", faces=("north",)),
        B("Dark", (1.25, 2.25, 13.5), (14.75, 9, 16), "black", faces=("north",)),
        B("HoodBack", (0.5, 0, 15.75), (15.5, 12.75, 16), "steel", faces=("south",)),
        # the weight display on a stalk, facing the passengers
        B("Stalk", (13.75, 3.5, 1.0), (14.5, 13, 1.75), "steel", faces=no("down")),
        B("DisplayBox", (11, 13, 0.75), (15.25, 16, 2.5), "darkplastic"),
        pic(B("Display", (11.5, 13.5, 0.5), (14.75, 15.5, 0.75), "black", faces=("north", "east", "west", "up", "down")), "north", "display", glow=150),
    ]
    els[-1]["faces"]["north"]["uv"] = [0, 0, 16, 16]
    return els


def checkin():
    def build(v):
        return checkin_desk() if v["part"] == "desk" else checkin_scale()

    def boxes(v):
        if v["part"] == "desk":
            return [(0, 0, 0, 1, 1.125, 1)]
        return [(0.03, 0, 0.03, 0.97, 0.14, 0.78), (0.03, 0, 0.78, 0.97, 0.8, 1)]

    def sel(v):
        if v["part"] == "desk":
            return [(0, 0, 0, 1, 1.125, 1)]
        return [(0.03, 0, 0.03, 0.97, 0.14, 0.78), (0.03, 0, 0.78, 0.97, 0.8, 1), (0.68, 0.14, 0.03, 0.96, 1.0, 0.16)]

    block("l36-checkin", [("part", ["desk", "scale"]), ("side", SIDES)], build,
          "Level 36: an airline check-in counter (desk: laminate front, kick plate, backlit LIMINAL AIR strip, the agent's monitor and "
          "printer behind, 18 px tall) and the baggage scale between two desks (tread plate, a belt into a hooded opening, a weight "
          "display); side = the passengers' side", boxes=boxes, sel=sel, material="Wood", sounds=WOOD)


# ======================================================================== 2. Gate seats

def gate_seat(kind):
    fab = "charcoal" if kind == "grey" else "navy"
    up = {"top": fab, "front": fab, "side": fab + "-side", "back": fab + "-side", "bottom": fab + "-side"}
    els = [
        # the shared floor beam, and this seat's leg and foot
        B("Beam", (0, 3, 8), (16, 4.5, 10), "steel", faces=("north", "south", "up", "down", "east", "west")),
        B("Leg", (7.25, 0.5, 8.25), (8.75, 3, 9.75), "chrome", faces=no("up", "down")),
        B("Foot", (5.75, 0, 6.5), (10.25, 0.5, 11.5), "darksteel", faces=no("down")),
        B("Bracket", (7, 4.5, 5), (9, 6, 12), "chrome", faces=no("up")),
        # the seat: a dark shell, an upholstered cushion with a rolled front
        B("Shell", (1.25, 6, 2.25), (14.75, 6.75, 12.5), "darksteel", faces=no("up")),
        B("Cushion", (1.25, 6.75, 2), (14.75, 8.75, 12.25), up, faces=no("down")),
        B("Roll", (1.25, 6.5, 1.5), (14.75, 8.5, 2), up, faces=no("south")),
        B("Spine", (7, 6, 12.5), (9, 10, 13.5), "chrome", faces=no("up", "down")),
    ]
    back = [B("BackShell", (1.25, 8.5, 12.5), (14.75, 19.5, 13.5), "darksteel"),
            B("BackCushion", (1.25, 9, 11.25), (14.75, 19, 12.5), up, faces=no("south"))]
    els += turned(back, rx=-8, origin=(8, 8.5, 12.5))
    # armrests on both sides (they meet the next seat's: a row reads as shared arms)
    for s, x in (("W", 0.25), ("E", 15.0)):
        els += [B(f"ArmPost{s}", (x, 4.5, 8.25), (x + 0.75, 12, 9.25), "chrome", faces=no("up", "down")),
                B(f"ArmBar{s}", (x, 11.25, 3.75), (x + 0.75, 12, 8.25), "chrome", faces=no("up", "south")),
                B(f"ArmPad{s}", (x - 0.25, 12, 3), (x + 1, 13, 11), "rubber")]
    if kind == "coat":
        els += turned([B("CoatTop", (2.25, 18.25, 10.5), (11.5, 20.25, 14.25), "jacket"),
                       B("CoatFrontL", (7.25, 11.5, 10.75), (11.5, 18.25, 11.0), "jacket", faces=no("south", "up")),
                       B("CoatFrontR", (2.25, 11.5, 10.75), (6.25, 18.25, 11.0), "jacket", faces=no("south", "up")),
                       B("Lining", (6.25, 12, 10.9), (7.25, 18.25, 11.1), "jacket-dark", faces=("north",)),
                       B("Hem", (2.25, 11.0, 10.6), (11.5, 11.5, 11.1), "jacket-dark", faces=no("south", "up")),
                       B("Pocket", (8.25, 13, 10.6), (10.5, 13.5, 10.75), "jacket-dark", faces=("north", "up", "east", "west")),
                       B("CoatBack", (2.75, 13, 13.75), (11, 18.25, 14.0), "jacket-dark", faces=no("north", "up")),
                       B("Collar", (2.5, 20.25, 11.25), (11.25, 20.75, 13.75), "jacket-dark", faces=no("down"))],
                      rx=-8, origin=(8, 8.5, 12.5))
        # the lapels, turned in toward the opening
        els += turned([B("LapelL", (7.25, 15.5, 10.5), (8.5, 18.75, 10.75), "jacket-dark", faces=no("south"))], rx=-8, rz=-14, origin=(7.25, 18, 11))
        els += turned([B("LapelR", (5.0, 15.5, 10.5), (6.25, 18.75, 10.75), "jacket-dark", faces=no("south"))], rx=-8, rz=14, origin=(6.25, 18, 11))
        els += turned([B("CoatSeat", (2, 8.75, 4.25), (11.5, 9.75, 11.25), "jacket", faces=no("down"))], ry=7, origin=(7, 8.75, 8))
        els += turned([B("Sleeve", (10.25, 3.5, 1.0), (12.25, 9.5, 2.5), "jacket", faces=no("up"))], rz=-7, origin=(11, 9.5, 2))
        els += turned([B("Cuff", (10.4, 2.75, 1.1), (12.1, 3.5, 2.4), "jacket-dark")], rz=-7, origin=(11, 9.5, 2))
        els += turned([B("SleeveL", (3, 9.75, 3.5), (5, 10.75, 9.5), "jacket")], ry=-24, origin=(4, 9.75, 6))
        els += turned([B("Shirt", (6.5, 9.75, 6), (10.5, 10.25, 10.5), "shirt", faces=no("down"))], ry=-15, origin=(8.5, 9.75, 8))
    elif kind == "bag":
        pack = {"front": "pack", "side": "pack", "top": "pack", "back": "pack-dark", "bottom": "pack-dark"}
        els += turned([
            B("Pack", (4, 8.75, 5.5), (12, 17.5, 10.5), pack),
            B("Pocket", (5, 9.25, 4.5), (11, 14, 5.5), "pack-dark", faces=no("south")),
            B("Zip", (5.25, 13.5, 4.35), (10.75, 13.75, 4.5), "black", faces=("north", "up")),
            B("Lid", (3.75, 16.75, 5.25), (12.25, 18.25, 10.75), "pack-dark"),
            B("Loop", (7.25, 18.25, 7.5), (8.75, 19, 8.5), "strap", faces=no("down")),
            B("StrapW", (5, 9.5, 10.5), (6.25, 17, 10.9), "strap", faces=no("north")),
            B("StrapE", (9.75, 9.5, 10.5), (11, 17, 10.9), "strap", faces=no("north")),
            B("Buckle", (7.4, 14.25, 4.3), (8.6, 15.25, 4.5), "black", faces=no("south")),
        ], rx=-6, ry=-8, origin=(8, 8.75, 10.5))
    return els


def seats():
    block("l36-seat", [("kind", ["blue", "grey", "coat", "bag"]), ("side", SIDES)], lambda v: gate_seat(v["kind"]),
          "Level 36's gates: a gate seat, one a block, on a floor beam shared along the row (navy or charcoal upholstery, chrome "
          "frame, armrests both sides); coat: a jacket left draped over a navy seat; bag: an abandoned backpack on one; side = "
          "the way a sitter faces",
          boxes=[(0, 0, 0.06, 1, 0.56, 0.78), (0, 0, 0.7, 1, 1.22, 0.9)], sel=[(0, 0, 0.06, 1, 1.22, 0.9)],
          material="Cloth", sounds=CLOTH)


# ======================================================================== 3. Gate podium

def gatedesk():
    grey = {"front": "termgrey", "side": "termgrey-side", "top": "termgrey-side", "back": "termgrey-side", "bottom": "termgrey-side"}

    def seg(x1, x2, n, dy=0.0):
        return [B(n + "Front", (x1, 0.75, 1.5), (x2, 19 - dy, 3), grey, faces=no("down", "up")),
                B(n + "Toe", (x1, 0, 2.25), (x2, 0.75, 3.75), "black", faces=("north", "up")),
                B(n + "Band", (x1, 4, 1.25), (x2, 4.5, 1.5), "steel", faces=("north", "up", "down")),
                B(n + "Cap", (x1, 19 - dy, 0.75), (x2, 20 - dy, 9.5), {"top": "steel", "front": "steel", "side": "steel", "back": "steel", "bottom": "termgrey-side"})]
    els = seg(4, 12, "M")
    # the ends curve back toward the agent (turned about the joints)
    els += turned(seg(-0.5, 4, "W", 0.03), ry=24, origin=(4, 0, 1.5))
    els += turned(seg(12, 16.5, "E", 0.03), ry=-24, origin=(12, 0, 1.5))
    els += [B("Shelf", (2, 12, 4.5), (14, 12.75, 9), "worktop"),
            B("Side", (2, 0, 3), (14, 12, 3.5), "termgrey-side", faces=("south",))]
    # a small screen on top, facing the back (the agent)
    els += turned([B("ScreenBox", (3, 20.5, 6.5), (9, 24.5, 7.5), "darkplastic"),
                   pic(B("Screen", (3.4, 20.9, 7.5), (8.6, 24.1, 7.7), "black", faces=("south", "east", "west", "up")), "south", "gatescreen", glow=120)],
                  rx=-12, origin=(6, 20.5, 7))
    els += [B("ScreenFoot", (4.5, 20, 6.25), (7.5, 20.5, 8.75), "darkplastic", faces=no("down")),
            B("ScreenNeck", (5.5, 20.5, 6.75), (6.5, 21.5, 7.25), "darkplastic", faces=no("up", "down"))]
    # the gooseneck PA microphone: a base, a stem bending over toward the agent, the mic head
    els += [B("MicBase", (10.5, 20, 6.5), (13, 20.5, 8.5), "black", faces=no("down")),
            B("MicSwitch", (11.25, 20.5, 7.75), (12.25, 20.75, 8.25), "darksteel", faces=no("down")),
            B("Stem0", (11.5, 20.5, 6.75), (12, 23, 7.25), "darksteel", faces=no("down"))]
    els += turned([B("Stem1", (11.5, 22.75, 6.75), (12, 25.5, 7.25), "darksteel", faces=no("down"))], rx=40, origin=(11.75, 22.9, 7))
    els += turned([B("Stem2", (11.5, 24.5, 9.0), (12, 26.25, 9.5), "darksteel", faces=no("down"))], rx=75, origin=(11.75, 24.75, 9.25))
    els += turned([B("MicHead", (11.3, 25.5, 10.0), (12.2, 26.4, 11.75), "black"),
                   B("MicGrille", (11.4, 25.6, 11.75), (12.1, 26.3, 12.0), "darksteel", faces=("south",))], rx=-10, origin=(11.75, 25.9, 10.5))
    return els


def gatedesks():
    block("l36-gatedesk", [("side", SIDES)], lambda v: gatedesk(),
          "Level 36's gates: the gate podium, a chest-high curved counter (the terminal's grey, a stainless edge), a screen on top and a "
          "gooseneck PA microphone, both toward the agent; side = the passengers' side",
          boxes=[(0, 0, 0.02, 1, 1.25, 0.62)], material="Wood", sounds=WOOD)


# ======================================================================== 4. Gate door (a wall cube)

def gatedoor(part):
    els = [B("Wall", (0, 0, 2), (16, 16, 16), "panel", faces=("east", "south", "west", "up", "down"))]
    upper = part == "upper"
    top = 12 if upper else 16
    # the stainless frame: jambs (and the head on the upper part)
    for s, (x1, x2) in (("W", (0, 2)), ("E", (14, 16))):
        els.append(B("Jamb" + s, (x1, 0, 0.5), (x2, top, 2), "steelv", faces=no("south", "up") if upper else no("south")))
    if upper:
        els.append(B("Head", (0, 12, 0.5), (16, 16, 2), "steel", faces=no("south")))
        # the status lamp over the window: a housing and a dark red lens
        els += [B("LampBox", (6.5, 12.75, 0.1), (9.5, 15.25, 0.5), "darksteel", faces=no("south")),
                B("Lamp", (7, 13.25, 0.0), (9, 14.75, 0.1), "lampred", faces=no("south"))]
        # the leaf round a small wired-glass window, and the GATE plate
        door = "door"
        wx1, wx2, wy1, wy2 = 5.5, 10.5, 2.5, 9.0
        els += [B("LeafB", (2, 0, 1.25), (14, wy1, 2), door, faces=("north", "up")),
                B("LeafT", (2, wy2, 1.25), (14, 12, 2), door, faces=("north", "down")),
                B("LeafL", (2, wy1, 1.25), (wx1, wy2, 2), door, faces=("north", "east")),
                B("LeafR", (wx2, wy1, 1.25), (14, wy2, 2), door, faces=("north", "west")),
                B("Glass", (wx1, wy1, 1.75), (wx2, wy2, 2), "wiredglass", faces=("north",), uv=(0, 0, 10, 13)),
                B("BeadT", (wx1 - 0.5, wy2, 0.75), (wx2 + 0.5, wy2 + 0.5, 1.25), "steel", faces=no("south")),
                B("BeadB", (wx1 - 0.5, wy1 - 0.5, 0.75), (wx2 + 0.5, wy1, 1.25), "steel", faces=no("south")),
                B("BeadL", (wx1 - 0.5, wy1, 0.75), (wx1, wy2, 1.25), "steel", faces=("north", "east", "west")),
                B("BeadR", (wx2, wy1, 0.75), (wx2 + 0.5, wy2, 1.25), "steel", faces=("north", "east", "west")),
                pic(B("Plate", (5.75, 9.875, 1.0), (10.25, 11.375, 1.25), "steel", faces=("north", "up", "down", "east", "west")), "north", "gateplate")]
    else:
        els.append(B("Leaf", (2, 0, 1.25), (14, 16, 2), "door", faces=("north",)))
        els.append(B("Sill", (0, 0, 0), (16, 0.25, 0.5), "steel", faces=("north", "up", "east", "west")))
        els += MK.push_bar("Push", 3, 13, 13.5, 1.25, tex="steel", depth=1.0)
        els += MK.kick_plate("Kick", 2.75, 13.25, 0.25, 5, 1.25, tex="steel")
        els += [B("Lock", (11.75, 15, 1.0), (12.75, 16, 1.25), "steel", faces=no("south")),
                B("LockCyl", (12.0, 15.25, 0.8), (12.5, 15.75, 1.0), "darksteel", faces=no("south"))]
    return els


def gatedoors():
    block("l36-gatedoor", [("part", ["lower", "upper"]), ("side", SIDES)], lambda v: gatedoor(v["part"]),
          "Level 36's holdrooms: the jet-bridge door set in the outer wall, a full wall cube (composite cladding on five faces, a heavy "
          "steel door in a stainless frame on <side>: lower with a push bar and kick plate, upper with a wired-glass window, a GATE "
          "plate and a dark red status lamp). Structure; BackroomsL36GateDoor boards flights",
          boxes=[(0, 0, 0, 1, 1, 1)], material="Metal", sounds=METAL,
          data={"sidesolid": {"all": True}, "sideopaque": {"all": True}, "lightAbsorption": 99, "resistance": 6,
                "behaviors": [{"name": "BackroomsL36GateDoor"}], "attributes": {"l36structure": True}})


# ======================================================================== 5. Stanchions

def stanchion(belt):
    els = octagon("Pad", 8, 8, 3.0, 0, 0.3, "rubber", faces=no("down", "up"))
    els += octagon("Base", 8, 8, 3.25, 0.3, 0.9, "chrome", faces=no("down"))
    els += octagon("Dome", 8, 8, 1.6, 0.9, 1.5, "chrome", faces=no("down"))
    els += octagon("Post", 8, 8, 0.6, 1.5, 12.5, "chrome", faces=no("down", "up"))
    els += [B("Head", (6.9, 12.5, 6.9), (9.1, 14.5, 9.1), "chrome"),
            B("Cap", (6.6, 14.5, 6.6), (9.4, 15, 9.4), "black", faces=no("down")),
            B("Ring", (7.0, 12.0, 7.0), (9.0, 12.5, 9.0), "black", faces=no("up"))]
    if belt != "none":
        # the belt out of the head's slot to the middle of the north edge (turned to the edge named)
        els += [B("Slot", (7.6, 12.75, 6.75), (8.4, 14.25, 6.9), "black", faces=("north",)),
                B("Belt", (7.875, 12.75, 0), (8.125, 14.25, 6.9), "beltnavy", faces=("east", "west", "up", "down"), uv=(0, 0, 6.9, 16))]
        for f in ("east", "west"):
            els[-1]["faces"][f]["uv"] = [0, 0, 6.9, 16]
    return els


def stanchions():
    post = (0.32, 0, 0.32, 0.68, 1.0, 0.68)
    belt_box = (0.45, 0, 0, 0.55, 1.0, 0.43)

    def boxes(v):
        return [post] if v["belt"] == "none" else [post, belt_box]

    def sel(v):
        p = (0.29, 0, 0.29, 0.71, 0.95, 0.71)
        return [p] if v["belt"] == "none" else [p, (0.45, 0.78, 0, 0.55, 0.9, 0.43)]

    block("l36-stanchion", [("belt", ["none"] + SIDES)], lambda v: stanchion(v["belt"]),
          "Level 36: a queue barrier, a chrome post at the block's centre with (unless none) its navy belt out to the middle of the "
          "edge named, so two blocks' belts meet in a line; collision 1.0 high on the post and the belt",
          boxes=boxes, sel=sel, rot="belt", material="Metal", sounds=METAL)


# ======================================================================== 6. Metal detector arch

def scanner(part):
    pan = {"front": "scangrey-side", "back": "scangrey-side", "side": "scangrey", "top": "scangrey-side", "bottom": "scangrey-side"}
    upper = part == "upper"
    h = 9.6 if upper else 16
    els = []
    for s, (x1, x2) in (("W", (0, 2)), ("E", (14, 16))):
        els.append(B("Panel" + s, (x1, 0, 3), (x2, h, 13), pan, faces=no("up", "down")))
        # rounded front and back edges: a slim strip standing proud of each end
        els.append(B("EdgeN" + s, (x1 + 0.25, 0, 2.5), (x2 - 0.25, h, 3), "scangrey-side", faces=no("up", "down", "south")))
        els.append(B("EdgeS" + s, (x1 + 0.25, 0, 13), (x2 - 0.25, h, 13.5), "scangrey-side", faces=no("up", "down", "north")))
        if not upper:
            # a foot plate, reaching a little into the walkway
            fx1, fx2 = (x1 + 0.1, x2 + 0.75) if s == "W" else (x1 - 0.75, x2 - 0.1)
            els.append(B("Foot" + s, (fx1, 0, 2), (fx2, 0.75, 14), "darksteel", faces=no("down")))
    # the indicator light strip down the front of the west panel (the viewer's right)
    if upper:
        els.append(pic(B("Lights", (0.5, 0.5, 2.25), (1.5, 8.5, 2.5), "black", faces=("north", "east", "west")), "north", "scanlight", glow=220))
        # the top beam: its underside at 9.6 (the opening 1.6 blocks), a little display on its front
        beam = {"front": "scangrey-side", "back": "scangrey-side", "side": "scangrey-side", "top": "scangrey", "bottom": "scangrey-side"}
        els += [B("Beam", (0, 9.6, 2.5), (16, 14, 13.5), beam),
                B("BeamCap", (0.25, 14, 2.75), (15.75, 14.5, 13.25), "scangrey", faces=no("down")),
                B("Window", (5.5, 10.6, 2.25), (10.5, 13, 2.5), "black", faces=("north", "east", "west", "up", "down")),
                B("Led", (9.25, 11.25, 2.15), (10, 12, 2.25), "scanlight", faces=("north",), glow=200, uv=(1, 13, 2.5, 13.75))]
    else:
        els.append(pic(B("Lights", (0.5, 7.5, 2.25), (1.5, 15.5, 2.5), "black", faces=("north", "east", "west")), "north", "scanlight", glow=220))
    return els


def scanners():
    def boxes(v):
        panels = [(0, 0, 0.16, 0.125, 1.0 if v["part"] == "lower" else 0.6, 0.84), (0.875, 0, 0.16, 1, 1.0 if v["part"] == "lower" else 0.6, 0.84)]
        return panels + ([(0, 0.6, 0.16, 1, 0.9, 0.84)] if v["part"] == "upper" else [])

    block("l36-scanner", [("part", ["lower", "upper"]), ("side", SIDES)], lambda v: scanner(v["part"]),
          "Level 36's security: a walk-through metal detector arch, two blocks tall (lower, upper): grey side panels on the block's left "
          "and right edges (walk through along the <side> axis), an indicator light strip, the top beam in the upper block (opening "
          "1.6 blocks); collision only on the panels and the beam",
          boxes=boxes, material="Metal", sounds=METAL)


# ======================================================================== 7. X-ray machine

def xray_body():
    body = "xraybody"
    inner = "xraydark"
    els = [
        B("Plinth", (1, 0, 0.75), (15, 1, 15.25), "black", faces=("north", "south", "east", "west")),
        B("Lower", (0.5, 1, 0), (15.5, 11.5, 16), body, faces=no("up", "down")),
        B("Bed", (2.5, 11.5, 0.4), (13.5, 12, 15.6), {"top": "beltrubber", "side": "darksteel"}, faces=("up", "north", "south")),
        B("WallW", (0.5, 11.5, 0.4), (2.5, 21, 15.6), {"west": body, "east": inner, "north": body, "south": body, "up": body, "down": body}, faces=no("up", "down")),
        B("WallE", (13.5, 11.5, 0.4), (15.5, 21, 15.6), {"east": body, "west": inner, "north": body, "south": body, "up": body, "down": body}, faces=no("up", "down")),
        B("Roof", (0.5, 21, 0.4), (15.5, 24, 15.6), {"down": inner, "all": body}),
        B("LedgeN", (0.5, 11.5, 0), (15.5, 11.5 + 0.5, 0.4), body, faces=("north", "up", "east", "west")),
        B("LedgeS", (0.5, 11.5, 15.6), (15.5, 12, 16), body, faces=("south", "up", "east", "west")),
    ]
    # trims round the tunnel mouths, and the lead-strip curtains inside them
    for s, z1, z2, f in (("N", 0, 0.4, "north"), ("S", 15.6, 16, "south")):
        els += [B("TrimT" + s, (1.5, 21, z1), (14.5, 22, z2), "darksteel", faces=(f, "down", "up", "east", "west")),
                B("TrimW" + s, (1.5, 12, z1), (2.5, 21, z2), "darksteel", faces=(f, "east", "west")),
                B("TrimE" + s, (13.5, 12, z1), (14.5, 21, z2), "darksteel", faces=(f, "east", "west")),
                ]
        # (round 4) the lead curtain as separate strips, one pushed back by the last bag through
        cz1, cz2 = (z1 + 1.0, z1 + 1.25) if s == "N" else (z2 - 1.25, z2 - 1.0)
        for i in range(5):
            x = 2.6 + i * 2.2
            strip = B(f"Curtain{s}{i}", (x, 12.5 + (i % 2) * 0.4, cz1), (x + 2.0, 21, cz2), "curtain", faces=("north", "south", "down"), uv=(0, 0, 2, 16))
            if i == 3:
                strip["rotationOrigin"] = [x + 1, 21, (cz1 + cz2) / 2]
                strip["rotationX"] = 22 if s == "N" else -22
            els.append(strip)
    els += [B("Gloom", (2.5, 12, 7.9), (13.5, 21, 8.1), "black", faces=("north", "south"))]
    # the yellow radiation sticker on the front, a panel seam
    els.append(pic(B("Sticker", (10.75, 22.25, 0.25), (12.75, 23.75, 0.4), body, faces=("north",)), "north", "radsticker"))
    # the operator's control panel and monitor on the east side
    els += [pic(B("Ctrl", (15.5, 4, 3), (16, 10, 11), "darksteel", faces=("east", "north", "south", "up", "down")), "east", "ctrlpanel"),
            B("MonPost", (13.25, 24, 7.25), (14.25, 26, 8.25), "darksteel", faces=no("down")),
            B("Monitor", (12.25, 25.5, 4.5), (13.75, 30, 11), "darkplastic"),
            pic(B("XScreen", (13.75, 26, 5), (14, 29.5, 10.5), "black", faces=("east",)), "east", "xrayscreen", glow=130),
            B("Beacon", (2.5, 24, 12.5), (4, 25, 14), "lampred", faces=no("down"))]
    return els


def xray_belt():
    els = [
        B("Bed", (2.5, 11, 0), (13.5, 11.75, 16), {"top": "rollers", "side": "darksteel"}, faces=("up", "down")),
        B("RailW", (1.5, 10, 0), (2.5, 12.5, 16), "steel", faces=no("north", "south")),
        B("RailE", (13.5, 10, 0), (14.5, 12.5, 16), "steel", faces=no("north", "south")),
    ]
    for i, z in enumerate((2, 13)):
        for s, x in (("W", 2), ("E", 13)):
            els += [B(f"Leg{s}{i}", (x, 0.5, z), (x + 1, 10, z + 1), "steelv", faces=no("up", "down")),
                    B(f"Foot{s}{i}", (x - 0.25, 0, z - 0.25), (x + 1.25, 0.5, z + 1.25), "rubber", faces=no("down"))]
        els.append(B(f"Brace{i}", (3, 3, z + 0.25), (13, 3.75, z + 0.75), "steel", faces=no("east", "west")))
    els.append(B("Stretcher", (2.25, 2.5, 3), (2.75, 3.25, 13), "steel", faces=no("north", "south")))
    # a grey tray on the rollers
    els += [B("TrayBase", (4, 11.75, 3.5), (12, 12.25, 11.5), {"top": "tray-in", "side": "tray"}, faces=no("down")),
            B("TrayN", (4, 12.25, 3.5), (12, 13.75, 4), "tray", faces=no("down")),
            B("TrayS", (4, 12.25, 11), (12, 13.75, 11.5), "tray", faces=no("down")),
            B("TrayW", (4, 12.25, 4), (4.5, 13.75, 11), "tray", faces=("east", "west", "up")),
            B("TrayE", (11.5, 12.25, 4), (12, 13.75, 11), "tray", faces=("east", "west", "up"))]
    return els


def xrays():
    def boxes(v):
        return [(0.03, 0, 0, 0.97, 1.5, 1)] if v["part"] == "body" else [(0.09, 0, 0, 0.91, 0.8, 1)]

    block("l36-xray", [("part", ["body", "belt"]), ("side", SIDES)], lambda v: xray_body() if v["part"] == "body" else xray_belt(),
          "Level 36's security: the X-ray baggage machine (body: a grey cabinet tunnel 1.5 blocks tall, bags pass along the <side> axis, "
          "lead-strip curtains, the operator's panel and monitor on its east side as modelled facing north) and the roller bed before "
          "and after it (belt: waist high on legs, a grey tray on it)",
          boxes=boxes, material="Metal", sounds=METAL)


# ======================================================================== 8. Tray stack

def trays():
    els = []
    n = 6
    for k in range(n):
        y0 = k * 1.3
        part = []
        if k < n - 1:
            part.append(B(f"Body{k}", (4, y0, 4.5), (12, y0 + 1.05, 11.5), "tray", faces=no("up") if k else no("up")))
            part.append(B(f"Lip{k}", (3.75, y0 + 1.05, 4.25), (12.25, y0 + 1.3, 11.75), "tray"))
        else:
            part += [B(f"Floor{k}", (4, y0, 4.5), (12, y0 + 0.3, 11.5), {"top": "tray-in", "side": "tray"}),
                     B(f"WallN{k}", (3.75, y0 + 0.3, 4.25), (12.25, y0 + 1.3, 4.75), "tray", faces=no("down")),
                     B(f"WallS{k}", (3.75, y0 + 0.3, 11.25), (12.25, y0 + 1.3, 11.75), "tray", faces=no("down")),
                     B(f"WallW{k}", (3.75, y0 + 0.3, 4.75), (4.25, y0 + 1.3, 11.25), "tray", faces=("east", "west", "up")),
                     B(f"WallE{k}", (11.75, y0 + 0.3, 4.75), (12.25, y0 + 1.3, 11.25), "tray", faces=("east", "west", "up"))]
        a = (-3, 2, -1, 4, -2, 1)[k]
        els += turned(part, ry=a, origin=(8, y0, 8)) if a else part
    return els


def tray_stack():
    block("l36-trays", [], lambda v: trays(),
          "Level 36's security: a stack of grey plastic security trays", boxes=[(0.22, 0, 0.25, 0.78, 0.5, 0.75)],
          rot=None, material="Wood", sounds=WOOD)


# ======================================================================== 9. Backrooms Travel Agency booth

def booth_desk():
    pur = {"front": "purple", "side": "purple-side", "top": "purple-side", "back": "purple-side", "bottom": "purple-side"}
    els = [
        B("Front", (0, 0.75, 1), (16, 15, 2.5), pur, faces=no("up", "down")),
        B("Toe", (0, 0, 1.75), (16, 0.75, 3.25), "black", faces=("north", "up")),
        B("TrimLow", (0, 0.75, 0.75), (16, 1.5, 1), "btawhite", faces=("north", "up", "east", "west")),
        B("TrimHigh", (0, 13.25, 0.75), (16, 13.75, 1), "btawhite", faces=("north", "up", "down", "east", "west")),
        pic(B("Logo", (4.5, 3.25, 0.75), (11.5, 10.25, 1.0), "btawhite", faces=("north", "up", "down", "east", "west")), "north", "btalogo"),
        B("Body", (0, 0, 2.5), (16, 15, 10), "purple-side", faces=("south",)),
        B("Top", (0, 15, 0.25), (16, 16, 11), {"top": "btawhite", "side": "btawhite", "front": "btawhite", "back": "btawhite", "bottom": "purple-side"}),
    ]
    # two acrylic brochure stands on the top, two leaflets each
    for i, x in enumerate((1.5, 9.5)):
        els += [B(f"Stand{i}", (x, 16, 2.5), (x + 5, 16.5, 6), "btawhite", faces=no("down"))]
        for j in range(2):
            lx = x + 0.25 + j * 2.5
            leaf = B(f"Leaf{i}{j}", (lx, 16.5, 4.5), (lx + 2.25, 20.5, 4.75), "btawhite", faces=("north", "south", "up", "east", "west"))
            pic(leaf, "north", f"leaflet-{(i * 2 + j) % 6}")
            els += turned([leaf], rx=-14, origin=(lx + 1.1, 16.5, 4.6))
        els += turned([B(f"StandBack{i}", (x, 16.5, 5.0), (x + 5, 19.5, 5.25), "btawhite", faces=("north", "south", "up", "east", "west"))],
                      rx=-14, origin=(x + 2.5, 16.5, 5.1))
    # a small bell and a stack of catalogues
    els += [B("Catalogue", (6.75, 16, 7), (9.75, 16.75, 9.5), {"top": "purple", "side": "btawhite"}, faces=no("down")),
            B("Catalogue2", (6.9, 16.75, 7.2), (9.6, 17.25, 9.3), {"top": "leaflet-4", "side": "btawhite"}, faces=no("down"))]
    return els


def booth_rack():
    els = [
        B("Base", (1.5, 0, 8), (14.5, 1.5, 13), "black", faces=no("down")),
        B("Back", (2.5, 1.5, 11), (13.5, 26, 12.25), {"front": "purple", "all": "purple-side"}, faces=no("up", "down")),
        B("PostW", (1.5, 1.5, 9.5), (2.5, 27, 12.5), "btawhite"),
        B("PostE", (13.5, 1.5, 9.5), (14.5, 27, 12.5), "btawhite"),
        B("Header", (1.5, 27, 9.5), (14.5, 31, 12.5), {"front": "purple", "all": "purple-side"}),
        pic(B("HeadLogo", (6.25, 27.25, 9.25), (9.75, 30.75, 9.5), "btawhite", faces=("north",)), "north", "btalogo"),
        B("HeadTrim", (1.5, 31, 9.25), (14.5, 31.5, 12.75), "btawhite", faces=no("down")),
    ]
    k = 0
    for r, y in enumerate((3, 7.75, 12.5, 17.25, 22)):
        els.append(B(f"Lip{r}", (2.5, y, 8.75), (13.5, y + 1.25, 9.25), "btawhite", faces=no("south")))
        els.append(B(f"Shelf{r}", (2.5, y - 0.5, 8.75), (13.5, y, 11), "btawhite", faces=("up", "down")))
        for c, (x1, x2) in enumerate(((2.75, 6.25), (6.5, 9.5), (9.75, 13.25))):
            k += 1
            if (r, c) == (3, 2):
                continue  # one pocket emptied
            leaf = B(f"Leaflet{r}{c}", (x1 + 0.25, y, 9.75), (x2 - 0.25, y + 4.0, 10.0), "btawhite", faces=("north", "up", "east", "west"))
            pic(leaf, "north", f"leaflet-{(r * 3 + c * 2) % 6}")
            els += turned([leaf], rx=-10, origin=((x1 + x2) / 2, y, 9.9))
    return els


def booth_sign(part):
    # the left, middle and right thirds as a viewer in front sees them; the back reads the other way round
    back = {"l": "r", "m": "m", "r": "l"}[part]
    trim = "btawhite"
    faces = ["north", "south", "up", "down"]
    if part == "l":
        faces.append("east")   # the viewer's left end (+X)
    if part == "r":
        faces.append("west")
    sign = B("Sign", (0, 4, 6.75), (16, 14, 9.25), trim, faces=tuple(faces))
    pic(sign, "north", f"btasign-{part}", glow=200)
    pic(sign, "south", f"btasign-{back}", glow=200)
    els = [sign]
    for i, x in enumerate((3.5, 12.5)):
        els += [B(f"Rod{i}", (x - 0.25, 14, 7.75), (x + 0.25, 15.75, 8.25), "chrome", faces=no("up", "down")),
                B(f"Rose{i}", (x - 0.75, 15.75, 7.25), (x + 0.75, 16, 8.75), "chrome", faces=no("up"))]
    return els


def booths():
    def build(v):
        p = v["part"]
        if p == "desk":
            return booth_desk()
        if p == "rack":
            return booth_rack()
        return booth_sign(p[-1])

    def boxes(v):
        p = v["part"]
        if p == "desk":
            return [(0, 0, 0.02, 1, 1.0, 0.7)]
        if p == "rack":
            return [(0.09, 0, 0.5, 0.91, 1.95, 0.82)]
        return None

    def sel(v):
        if v["part"].startswith("sign"):
            return [(0, 0.25, 0.42, 1, 1.0, 0.58)]
        return boxes(v)

    light = {f"l36-booth-{p}-{s}": [48, 5, 6] for p in ("signl", "signm", "signr") for s in SIDES}
    block("l36-booth", [("part", ["desk", "rack", "signl", "signm", "signr"]), ("side", SIDES)], build,
          "Level 36's check-in hall: the Backrooms Travel Agency booth, booth 0 (desk: a purple counter, white trim, the BTA logo, brochure "
          "stands; rack: a tall brochure rack; signl/signm/signr: a three-block backlit fascia sign, BACKROOMS TRAVEL AGENCY, read left "
          "to right facing <side>, hung from the top of its block, no collision, faint purple light)",
          boxes=boxes, sel=sel, material="Wood", sounds=WOOD, data={"lightHsvByType": light})


# ======================================================================== 10. Perfume counter

def perfume():
    wht = {"front": "white", "side": "white-side", "top": "white-side", "back": "white-side", "bottom": "white-side"}
    els = [
        B("Toe", (1, 0, 1.75), (15, 0.75, 13.5), "black", faces=("north", "east", "west", "up")),
        B("Base", (0.5, 0.75, 1), (15.5, 9, 14), wht, faces=no("down")),
        B("Gold", (0.5, 8.25, 0.75), (15.5, 8.75, 1), "gold", faces=("north", "up", "down", "east", "west")),
        B("Floor", (1, 9, 1.5), (15, 9.25, 13.5), "white", faces=("up",)),
    ]
    # the glass case: panes in the transparent pass, steel corner posts
    els += [transparent(B("GlassN", (1, 9, 1.25), (15, 14, 1.45), "glass", faces=("north", "south"))),
            transparent(B("GlassW", (1, 9, 1.5), (1.2, 14, 13.5), "glass", faces=("east", "west"))),
            transparent(B("GlassE", (14.8, 9, 1.5), (15, 14, 13.5), "glass", faces=("east", "west"))),
            transparent(B("GlassTop", (1, 14, 1.25), (15, 14.25, 13.75), "glass", faces=("up", "down")))]
    for s, (x, z) in (("NW", (0.75, 1.0)), ("NE", (14.75, 1.0)), ("SW", (0.75, 13.25)), ("SE", (14.75, 13.25))):
        els.append(B("Post" + s, (x, 9, z), (x + 0.5, 14.5, z + 0.5), "steelv", faces=no("down")))
    els.append(B("Back", (1, 9, 13.4), (15, 14, 13.65), "white", faces=("north", "south")))
    # rows of tinted bottles in the case: pink, amber, blue, green
    cols = ["pink", "amber", "blue", "green"]
    shapes_ = [(1.4, 3.2), (1.8, 2.4), (1.2, 3.6), (2.0, 2.0), (1.5, 2.8)]
    i = 0
    for r, z in enumerate((4.0, 8.5)):
        for c, x in enumerate((2.0, 4.6, 7.2, 9.8, 12.4)):
            w, h = shapes_[(c + r * 2) % len(shapes_)]
            col = cols[(c + r) % 4]
            x1, z1 = x + (2 - w) / 2, z + (2 - w) / 2
            els += [B(f"Bottle{i}", (x1, 9.25, z1), (x1 + w, 9.25 + h, z1 + w), f"bottle-{col}", faces=no("down")),
                    B(f"Neck{i}", (x + 0.75, 9.25 + h, z + 0.75), (x + 1.25, 9.25 + h + 0.4, z + 1.25), f"bottle-{col}", faces=no("down", "up")),
                    B(f"Cap{i}", (x + 0.6, 9.25 + h + 0.4, z + 0.6), (x + 1.4, 9.25 + h + 1.0, z + 1.4), "gold", faces=no("down"))]
            i += 1
    # testers on the glass top, a TESTER card
    els += [B("TestTray", (8.5, 14.25, 8.5), (14.5, 14.5, 13), "white", faces=no("down"))]
    for j, (x, col) in enumerate(((9.25, "pink"), (11.25, "blue"), (13.0, "amber"))):
        els += [B(f"Tester{j}", (x, 14.5, 10), (x + 1.25, 16.75, 11.25), f"bottle-{col}", faces=no("down")),
                B(f"TCap{j}", (x + 0.25, 16.75, 10.25), (x + 1.0, 17.25, 11.0), "gold", faces=no("down"))]
    els += turned([pic(B("Card", (9, 14.5, 9.0), (12, 16, 9.25), "white", faces=("north", "south", "up", "east", "west")), "north", "tester")],
                  rx=-15, origin=(10.5, 14.5, 9.1))
    return els


def perfumes():
    block("l36-perfume", [("side", SIDES)], lambda v: perfume(),
          "Level 36's duty-free: a perfume display counter, glass-topped white, rows of tinted bottles (pink, amber, blue, green) and "
          "testers on top. The perfume is tinted water: worthless",
          boxes=[(0.03, 0, 0.05, 0.97, 0.94, 0.88)], material="Glass", sounds=GLASS)


# ======================================================================== 11. Food court tables

def meal_table(kind):
    els = octagon("Top", 8, 8, 6.0, 11.2, 12.0, {"top": "tabletop", "bottom": "tableedge", "side": "tableedge"})
    els += octagon("Band", 8, 8, 5.85, 10.5, 11.2, "tableedge", faces=("north", "east", "south", "west", "down"))
    els += [B("SpiderA", (4.0, 9.9, 7.5), (12.0, 10.5, 8.5), "chrome", faces=("north", "south", "east", "west", "down")),
            B("SpiderB", (7.5, 9.9, 4.0), (8.5, 10.5, 12.0), "chrome", faces=("north", "south", "east", "west", "down"))]
    els += octagon("Collar", 8, 8, 1.35, 8.6, 9.9, "chrome")
    els += octagon("Column", 8, 8, 0.85, 1.4, 8.6, "chrome", faces=("north", "east", "south", "west"))
    els += octagon("Hub", 8, 8, 1.5, 0.4, 1.6, "darksteel")
    els += [B("FootA", (2.6, 0.5, 7.4), (13.4, 1.1, 8.6), "darksteel", faces=("north", "south", "east", "west", "up")),
            B("FootB", (7.4, 0.5, 2.6), (8.6, 1.1, 13.4), "darksteel", faces=("north", "south", "east", "west", "up"))]
    for i, (x, z) in enumerate(((3.2, 8), (12.8, 8), (8, 3.2), (8, 12.8))):
        els.append(B(f"Glide{i}", (x - 0.7, 0, z - 0.7), (x + 0.7, 0.5, z + 0.7), "rubber"))
    T = 12.0
    if kind == "tray":
        tray = [B("Tray", (3.5, T, 4.5), (11.5, T + 0.4, 10.5), "foodtray", faces=no("down"))]
        tray += MK.rim("TrayRim", (3.5, T, 4.5), (11.5, T + 0.4, 10.5), "foodtray", w=0.5, h=0.4)
        tray += [B("Wrapper", (4.25, T + 0.4, 5.25), (8.75, T + 0.5, 9.75), "napkin", faces=("up", "north", "south", "east", "west")),
                 B("BunLow", (5, T + 0.5, 6), (8, T + 1.25, 9), "bun", faces=no("down")),
                 B("Patty", (4.9, T + 1.25, 5.9), (8.1, T + 1.9, 9.1), "patty", faces=no("down")),
                 B("Lettuce", (4.8, T + 1.9, 5.8), (8.2, T + 2.1, 9.1), "lettuce", faces=no("down")),
                 # the top bun bitten: two pieces, a bite out of the north-west quarter
                 B("BunTopA", (5, T + 2.1, 7.5), (8, T + 3.2, 9), "bun", faces=no("down")),
                 B("BunTopB", (6.5, T + 2.1, 6), (8, T + 3.0, 7.5), "bun", faces=no("down")),
                 B("Fries", (9, T + 0.4, 5.5), (10.75, T + 2.5, 7), "foodtray", faces=no("down")),
                 B("Fry0", (9.25, T + 2.5, 5.75), (9.6, T + 3.4, 6.1), "bun", faces=no("down")),
                 B("Fry1", (10.0, T + 2.5, 6.25), (10.35, T + 3.1, 6.6), "bun", faces=no("down"))]
        els += turned(tray, ry=12, origin=(7.5, T, 7.5))
        els += turned([B("Napkin0", (10.25, T, 9.25), (12.25, T + 0.9, 11.0), "napkin", faces=no("down"))], rx=12, ry=35, origin=(11.25, T, 10.1))
        els += turned([B("Napkin1", (10.6, T + 0.4, 9.6), (11.9, T + 1.4, 10.8), "napkin", faces=no("down"))], rz=25, ry=-20, origin=(11.25, T + 0.5, 10.2))
    elif kind == "cups":
        for i, (cx, cz, ang) in enumerate(((5.5, 6.5, 30), (9.75, 9.5, -40))):
            els += octagon(f"Cup{i}", cx, cz, 1.05, T, T + 3.4, "cup", faces=no("down", "up"))
            els += octagon(f"Lid{i}", cx, cz, 1.25, T + 3.4, T + 3.8, "white", faces=no("down"))
            s = 0.18
            els.append(B(f"Straw{i}a", (cx - s, T + 3.8, cz - s), (cx + s, T + 6.0, cz + s), "straw", faces=no("down")))
            # the soggy paper straw bends over and kinks again
            els += turned([B(f"Straw{i}b", (cx - s, T + 5.9, cz - s), (cx + s, T + 7.6, cz + s), "straw", faces=no("down"))],
                          rx=ang, ry=25 * (1 if i else -1), origin=(cx, T + 5.95, cz))
        els += turned([B("Wrapper", (6.5, T, 9.5), (8.5, T + 0.25, 10.25), "napkin", faces=no("down"))], ry=20, origin=(7.5, T, 9.9))
        els += turned([B("Ring", (4, T, 9.5), (5.5, T + 0.05, 11), "foodtray", faces=("up",))], ry=10, origin=(4.75, T, 10.25))
    elif kind == "plate":
        els += octagon("Plate", 7.5, 7.5, 3.6, T, T + 0.3, "plate", faces=no("down"))
        els += octagon("PlateRim", 7.5, 7.5, 3.9, T + 0.3, T + 0.55, "plate", faces=no("down", "up"))
        els += [B("Food", (5.5, T + 0.3, 5.75), (9.5, T + 1.5, 9.25), "mould", faces=no("down")),
                B("Fuzz0", (6, T + 1.5, 6.25), (8.25, T + 2.1, 8.25), "mould", faces=no("down")),
                B("Fuzz1", (8, T + 1.5, 7.25), (9.25, T + 1.9, 8.75), "mould", faces=no("down")),
                B("Smear", (4.75, T + 0.3, 8.5), (6, T + 0.45, 9.75), "mould", faces=("up", "north", "east", "west", "south"))]
        els += turned([B("Fork", (10.75, T, 6.5), (11.25, T + 0.25, 11.5), "chrome", faces=no("down")),
                       B("Tines", (10.6, T, 5.5), (11.4, T + 0.25, 6.5), "chrome", faces=no("down"))], ry=-18, origin=(11, T, 8.5))
        els += turned([B("Cup", (3.5, T, 10.5), (5.25, T + 2.5, 12.25), "cup", faces=no("down"))], ry=8, origin=(4.4, T, 11.4))
    return els


def meal_tables():
    block("l36-mealtable", [("kind", ["tray", "cups", "plate", "clean"])], lambda v: meal_table(v["kind"]),
          "Level 36's food courts: a round pedestal cafe table, white top on grey and chrome, with what was left on it (tray: a burger "
          "half eaten and a crumpled napkin; cups: two paper cups, their paper straws bent and soggy; plate: something gone mouldy; "
          "clean: bare)", boxes=[(0.12, 0, 0.12, 0.88, 0.75, 0.88)], rot=None, material="Wood", sounds=WOOD)


# ======================================================================== 12. Meeting Place column

def meeting(part):
    col = "steelv"
    if part == "base":
        return [B("Plinth", (1, 0, 1), (15, 1.5, 15), "darksteel", faces=no("down", "up")),
                B("PlinthTop", (1.25, 1.5, 1.25), (14.75, 2, 14.75), "steel", faces=no("down")),
                B("Column", (2, 2, 2), (14, 16, 14), col, faces=no("down"))]
    if part == "mid":
        return [B("ColumnLow", (2, 0, 2), (14, 7.75, 14), col, faces=no("down", "up")),
                B("Seam", (2.25, 7.75, 2.25), (13.75, 8.25, 13.75), "seamlight", faces=SIDE4, glow=255),
                B("ColumnHigh", (2, 8.25, 2), (14, 16, 14), col, faces=no("down"))]
    els = [B("Column", (2, 0, 2), (14, 4, 14), col, faces=no("down", "up")),
           B("Under", (1, 3.5, 1), (15, 4.5, 15), "steel", faces=no("up")),
           B("Cap", (0.75, 15, 0.75), (15.25, 15.75, 15.25), "steel")]
    sign = B("Sign", (1, 4.5, 1), (15, 15, 15), "steel", faces=SIDE4)
    for f in SIDE4:
        pic(sign, f, "meetsign", glow=255, uv=(0, 0, 16, 16))
    els.append(sign)
    for s, (x, z) in (("NW", (0.75, 0.75)), ("NE", (14.25, 0.75)), ("SW", (0.75, 14.25)), ("SE", (14.25, 14.25))):
        els.append(B("Edge" + s, (x, 4.5, z), (x + 1, 15, z + 1), "steel", faces=SIDE4))
    return els


def meetings():
    def boxes(v):
        if v["part"] == "base":
            return [(0.06, 0, 0.06, 0.94, 0.125, 0.94), (0.125, 0, 0.125, 0.875, 1, 0.875)]
        if v["part"] == "top":
            return [(0.05, 0, 0.05, 0.95, 1, 0.95)]
        return [(0.125, 0, 0.125, 0.875, 1, 0.875)]

    block("l36-meetingpoint", [("part", ["base", "mid", "top"])], lambda v: meeting(v["part"]),
          "Level 36: the Meeting Place marker, a three-block column of brushed stainless (base with a plinth, mid with a thin lit seam, "
          "top a lit cube sign on four faces: four white arrows converging on a dot, on red; light 10 from the top)",
          boxes=boxes, rot=None, material="Metal", sounds=METAL,
          data={"lightHsvByType": {"l36-meetingpoint-top": [0, 5, 10], "l36-meetingpoint-mid": [40, 1, 3]}})


# ======================================================================== 13. Economy seat

def cabin_seat():
    cab = {"top": "cabin", "front": "cabin", "side": "cabin-side", "back": "cabin-side", "bottom": "cabin-side"}
    els = []
    for i, (x, z) in enumerate(((2.5, 3.5), (12.5, 3.5), (2.5, 10.5), (12.5, 10.5))):
        els.append(B(f"Leg{i}", (x, 0.5, z), (x + 1, 5.5, z + 1), "steelv", faces=no("up", "down")))
        els.append(B(f"Foot{i}", (x - 0.25, 0, z - 0.5), (x + 1.25, 0.5, z + 1.5), "darksteel", faces=no("down")))
    els += [B("SpreaderF", (2.5, 4.25, 3.75), (13.5, 5, 4.25), "steel", faces=no("east", "west")),
            B("SpreaderB", (2.5, 4.25, 10.75), (13.5, 5, 11.25), "steel", faces=no("east", "west")),
            B("Pan", (1.75, 5.5, 2.5), (14.25, 6.25, 12.5), "darkplastic", faces=no("up")),
            B("Cushion", (1.75, 6.25, 1.75), (14.25, 8.75, 12.25), cab, faces=no("down")),
            B("Roll", (1.75, 6.0, 1.25), (14.25, 8.5, 1.75), cab, faces=no("south")),
            B("Vest", (4.5, 4.5, 2.25), (11.5, 5.5, 3.75), "darkplastic", faces=no("up"))]
    back = [B("Shell", (1.75, 7.5, 13), (14.25, 24, 14.25), {"back": "darkplastic", "all": "darkplastic"}),
            B("Back", (1.75, 8.5, 11.5), (14.25, 23, 13), cab, faces=no("south")),
            # the white headrest cover, over the top
            B("Cover", (2.75, 18.5, 11.25), (13.25, 23.25, 11.5), "headcover", faces=no("south")),
            B("CoverTop", (2.75, 23.25, 11.25), (13.25, 24.4, 14.5), "headcover", faces=no("down")),
            B("CoverBack", (2.75, 21, 14.25), (13.25, 23.25, 14.5), "headcover", faces=no("north", "up")),
            # the folded tray table and its latch, a seat pocket under it
            B("Tray", (3, 13.25, 14.25), (13, 19.75, 14.75), "lightplastic", faces=no("north")),
            B("Latch", (7.25, 19.75, 14.25), (8.75, 20.5, 14.85), "darkplastic", faces=no("north")),
            B("Pocket", (3, 8.5, 14.25), (13, 12.5, 14.85), "cabin-side", faces=no("north")),
            B("Card", (4, 12.5, 14.4), (6.5, 13.6, 14.6), "leaflet-1", faces=("south", "up", "north"))]
    els += turned(back, rx=-10, origin=(8, 8, 12.5))
    # armrests on both sides
    for s, x in (("W", 0.5), ("E", 14.25)):
        els += [B(f"ArmPost{s}", (x + 0.2, 5, 9.5), (x + 1.05, 11.5, 10.75), "darkplastic", faces=no("up", "down")),
                B(f"Arm{s}", (x, 11.5, 3.5), (x + 1.25, 12.75, 12.75), "darkplastic"),
                B(f"ArmCap{s}", (x + 0.1, 12.75, 4), (x + 1.15, 13, 12.25), "rubber", faces=no("down"))]
    # the seatbelt lying across the seat, buckled
    els += [B("BeltW", (1.75, 8.75, 6.25), (7.25, 9.0, 7.75), "webgrey", faces=no("down")),
            B("BeltE", (8.75, 8.75, 6.25), (14.25, 9.0, 7.75), "webgrey", faces=no("down")),
            B("Buckle", (7.0, 8.75, 6.0), (9.0, 9.25, 8.0), "chrome", faces=no("down")),
            B("BeltDropW", (1.6, 6.5, 6.25), (1.75, 8.85, 7.75), "webgrey", faces=("west",)),
            B("BeltDropE", (14.25, 6.5, 6.25), (14.4, 8.85, 7.75), "webgrey", faces=("east",))]
    return els


def cabin_seats():
    block("l36-cabinseat", [("side", SIDES)], lambda v: cabin_seat(),
          "Level 36's plane cabin: an airline economy seat (navy cloth, white headrest cover, armrests, a folded tray table on its back, the "
          "seatbelt buckled across the seat); side = the way a sitter faces",
          boxes=[(0.03, 0, 0.06, 0.97, 0.56, 0.8), (0.06, 0, 0.72, 0.94, 1.5, 0.95)], sel=[(0.03, 0, 0.06, 0.97, 1.5, 0.95)],
          material="Cloth", sounds=CLOTH)


# ======================================================================== 14. Lost & Found shelf

def lost_found():
    els = []
    # a steel shelving unit: four uprights and four shelves
    for s, (x, z) in (("NW", (0.25, 2.75)), ("NE", (14.75, 2.75)), ("SW", (0.25, 14.75)), ("SE", (14.75, 14.75))):
        els.append(B("Up" + s, (x, 0, z), (x + 1, 16, z + 1), "shelf", faces=no("down")))
    for i, y in enumerate((0.75, 6, 11, 15.25)):
        els.append(B(f"Shelf{i}", (0.75, y, 3), (15.25, y + 0.5, 15.25), "shelf"))
        els.append(B(f"ShelfLip{i}", (0.75, y - 0.5, 3), (15.25, y, 3.25), "shelf", faces=("north", "down")))
    els += [B("BraceW", (0.5, 1, 15.0), (0.75, 15.25, 15.25), "shelf", faces=("west", "north")),
            B("BraceE", (15.25, 1, 15.0), (15.5, 15.25, 15.25), "shelf", faces=("east", "north"))]
    # bottom tier (1.25-6): a red hard case lying flat, a duffel bag
    els += [B("CaseRed", (1.25, 1.25, 3.75), (8, 4.5, 14), "case-red", faces=no("down")),
            B("CaseRedHandle", (3.5, 2.25, 3.25), (5.75, 3.25, 3.75), "black", faces=no("south")),
            B("CaseTeal", (2, 4.5, 4.75), (7.5, 5.75, 13), "case-teal", faces=no("down")),
            B("Duffel", (8.75, 1.25, 4.25), (14.5, 5.25, 14.25), "duffel", faces=no("down")),
            B("DuffelEnd", (8.5, 1.75, 4.0), (14.75, 4.75, 4.25), "duffel", faces=no("south")),
            B("DuffelStrap", (11, 5.25, 4.0), (12, 5.75, 14.5), "strap", faces=no("down")),
            pic(B("Tag0", (5.5, 1.75, 3.5), (6.75, 3.25, 3.6), "tag", faces=("north", "south")), "north", "tag")]
    # middle tier (6.5-11): an upright blue case, a backpack, a leather bag
    els += [B("CaseBlue", (1.25, 6.5, 5), (5.5, 10.75, 14), "case-blue", faces=no("down")),
            B("CaseBlueHandle", (2.75, 10.75, 8.5), (4, 11, 10.5), "black", faces=no("down")),
            B("Pack", (6, 6.5, 6), (10, 10.5, 12), {"front": "pack", "side": "pack", "top": "pack-dark", "back": "pack-dark"}, faces=no("down")),
            B("PackPocket", (6.75, 7, 5.25), (9.25, 9.5, 6), "pack-dark", faces=no("south")),
            B("Handbag", (10.75, 6.5, 5), (14.5, 9.5, 9), "leather", faces=no("down")),
            B("HandbagLoop", (11.75, 9.5, 6.75), (13.5, 10.75, 7.25), "leather", faces=no("down", "north", "south")),
            B("HandbagLoopIn", (12.25, 9.5, 6.75), (13.0, 10.25, 7.25), "black", faces=("north", "south")),
            pic(B("Tag1", (1.0, 7.5, 9), (1.25, 9, 10.25), "tag", faces=("east", "west")), "west", "tag")]
    # top tier (11.5-15.25): a black case on its side, a silver case, umbrellas lying across
    els += [B("CaseBlack", (1.25, 11.5, 4), (7.25, 15.0, 12.5), "case-black", faces=no("down")),
            B("CaseSilver", (8, 11.5, 5.5), (13, 14.5, 14.5), "case-silver", faces=no("down"))]
    els += turned([B("Umbrella0", (2, 15.75, 5), (14, 16.75, 6), "umbrella", faces=no("down")),
                   B("Handle0", (14, 15.75, 5.1), (15.25, 16.65, 5.9), "leather", faces=no("down"))], ry=-6, origin=(8, 15.75, 5.5))
    els += turned([B("Umbrella1", (3, 15.75, 8), (13.5, 16.5, 9), "umbrella", faces=no("down")),
                   B("Handle1", (1.75, 15.75, 8.1), (3, 16.4, 8.9), "black", faces=no("down"))], ry=9, origin=(8, 15.75, 8.5))
    # the placard on the top shelf's front
    els.append(pic(B("Placard", (3, 15.75, 2.5), (13, 18.25, 2.9), "shelf", faces=("north", "south", "up", "east", "west")), "north", "lfsign"))
    els.append(B("PlacardFoot", (5, 15.75, 2.9), (11, 16.25, 4), "shelf", faces=no("down")))
    # an umbrella leaning against the right upright
    els += turned([B("Lean", (14.75, 0.25, 1.5), (15.75, 13.5, 2.5), "umbrella"),
                   B("LeanTip", (15.0, 0, 1.75), (15.5, 0.25, 2.25), "steel", faces=no("down")),
                   B("LeanHandle", (15.0, 13.5, 1.75), (15.5, 15.5, 2.25), "leather")], rz=6, origin=(15.25, 0, 2))
    return els


def lost_founds():
    block("l36-lostfound", [("side", SIDES)], lambda v: lost_found(),
          "Level 36's baggage claim: a Lost & Found shelf unit crammed with suitcases, bags and umbrellas (luggage left on a carousel ten "
          "rounds ends up here), against the wall behind it",
          boxes=[(0, 0, 0.15, 1, 1, 1)], material="Wood", sounds=WOOD)


# ======================================================================== The links (2026-10-31)

def airportdoor(part):
    """A glazed aluminium door, flush in a full block of wall: the terminal's own way out to the curb (and, found in a wall of
    the city or the Suburbs, its way in). Modelled facing north; the frame recessed half a pixel to two."""
    upper = part == "upper"
    cut = "down" if upper else "up"
    els = [B("Wall", (0, 0, 2), (16, 16, 16), "darksteel", faces=("east", "south", "west", "up", "down"))]
    for s, (x1, x2) in (("W", (0, 1.5)), ("E", (14.5, 16))):
        els.append(B("Jamb" + s, (x1, 0, 0.5), (x2, 16, 2), "steelv", faces=no("south", cut)))
    top = 11.5 if upper else 16
    for s, (x1, x2) in (("W", (1.5, 3)), ("E", (13, 14.5))):
        els.append(B("Stile" + s, (x1, 0, 1.0), (x2, top, 2), "steelv", faces=no("south", "down") if upper else no("south", "up")))
    if upper:
        els += [B("TopRail", (3, 10, 1.0), (13, 11.5, 2), "steel", faces=no("south")),
                B("Glass", (3, 0, 1.6), (13, 10, 1.8), "airglass", faces=("north",), uv=(0, 6, 10, 16)),
                B("Transom", (1.5, 11.5, 1.6), (14.5, 13, 1.8), "airglass", faces=("north",), uv=(0, 0, 13, 1.5)),
                B("Head", (0, 13, 0.5), (16, 16, 2), "steel", faces=no("south"))]
    else:
        els += [B("Kick", (3, 0, 1.0), (13, 4, 2), "steel", faces=no("south", "down")),
                B("Glass", (3, 4, 1.6), (13, 16, 1.8), "airglass", faces=("north",), uv=(0, 0, 10, 12)),
                B("Sill", (0, 0, 0), (16, 0.25, 0.5), "steel", faces=("north", "up", "east", "west")),
                B("BarL", (3.5, 8.25, 0.9), (4.25, 9.25, 1.6), "chrome", faces=no("south")),
                B("BarR", (11.75, 8.25, 0.9), (12.5, 9.25, 1.6), "chrome", faces=no("south")),
                B("Bar", (3.5, 8.25, 0.4), (12.5, 9.25, 0.9), "chrome", faces=no("south"))]
    return els


def airportsign():
    """The backlit sign over the door: a full block of wall with the lit sign face on its front."""
    return [B("Wall", (0, 0, 2), (16, 16, 16), "darksteel", faces=("east", "south", "west", "up", "down")),
            pic(B("Face", (0, 0, 0), (16, 16, 2), "darksteel", faces=("north", "east", "west", "up", "down")), "north", "airsign", glow=160)]


def sink(state):
    """A restroom washbasin: a laminate vanity, a stone top, a white vessel bowl, a chrome tap from the splashback. Running
    over: water to the rim, over the front, down the vanity and out across the floor."""
    lam = {"front": "laminate", "side": "laminate-side", "top": "laminate-side", "back": "laminate-side", "bottom": "laminate-side"}
    bowl_n = {"front": "white", "side": "white-side", "top": "white", "back": "white-side", "bottom": "white"}
    bowl_s = {"front": "white-side", "side": "white-side", "top": "white", "back": "white", "bottom": "white"}
    els = [B("Body", (0, 0, 4), (16, 11, 16), lam, faces=("north", "east", "west")),
           B("Top", (0, 11, 3), (16, 12.5, 16), "worktop", faces=no("south")),
           B("Splash", (0, 12.5, 15), (16, 16, 16), "white", faces=("north", "east", "west", "up")),
           # the bowl: four walls and a floor
           B("BowlN", (3.5, 12.5, 5), (12.5, 15.5, 5.75), bowl_n, faces=no("down")),
           B("BowlS", (3.5, 12.5, 12.25), (12.5, 15.5, 13), bowl_s, faces=no("down")),
           B("BowlW", (3.5, 12.5, 5.75), (4.25, 15.5, 12.25), "white-side", faces=("east", "west", "up")),
           B("BowlE", (11.75, 12.5, 5.75), (12.5, 15.5, 12.25), "white-side", faces=("east", "west", "up")),
           B("BowlFloor", (4.25, 12.5, 5.75), (11.75, 13.25, 12.25), "basin", faces=("up",), uv=(0, 0, 16, 16)),
           # the tap
           B("TapPost", (7.25, 12.5, 13.5), (8.75, 15.25, 15), "chrome", faces=no("down", "south")),
           B("Spout", (7.5, 14.5, 10.25), (8.5, 15.25, 13.5), "chrome", faces=no("south")),
           B("Lever", (7.75, 15.25, 13.75), (8.25, 15.75, 14.75), "chrome", faces=no("down")),
           # (round 4) the mirror over it on the wall, in a steel frame, a soap dispenser beside the tap
           # (the basins stand free in the middle of the restrooms: the mirror is on a panel standing up from the splashback)
           B("MirrorPanel", (0.5, 16, 15.5), (15.5, 31.75, 16), "white-side", faces=("south", "east", "west", "up")),
           B("MirrorFrame", (1, 18, 15.25), (15, 31, 15.5), "chrome", faces=("north", "up", "down", "east", "west")),
           B("Mirror", (1.75, 18.75, 15.1), (14.25, 30.25, 15.25), "r4-mirror", faces=("north",)),
           B("Soap", (11.5, 17, 14.25), (13.5, 21, 15.25), "white", faces=no("south")),
           B("SoapNozzle", (12.25, 16.5, 13.5), (12.75, 17, 14.5), "chrome", faces=no("south"))]
    if state == "overflow":
        els += [B("Water", (4.25, 15.25, 5.75), (11.75, 15.35, 12.25), "water", faces=("up",)),
                B("Stream", (7.6, 13.25, 10.3), (8.4, 14.5, 11.1), "waterfall", faces=("north", "east", "west")),
                B("SpillRim", (5, 15.5, 4.85), (11, 15.6, 5.75), "water", faces=("up", "north")),
                B("SpillBowl", (5, 12.5, 4.85), (11, 15.5, 4.95), "waterfall", faces=("north",)),
                B("SpillTop", (4.5, 12.5, 2.85), (11.5, 12.6, 4.85), "water", faces=("up",)),
                B("SpillLip", (4.5, 11, 2.85), (11.5, 12.5, 2.95), "waterfall", faces=("north",)),
                B("SpillFront", (5, 0.1, 3.85), (11, 11, 3.95), "waterfall", faces=("north",)),
                B("Puddle", (1, 0, -7), (15, 0.12, 4), "water", faces=("up",))]
    return els


def link_blocks():
    door = {"sidesolid": {"all": True}, "sideopaque": {"all": True}, "lightAbsorption": 99, "resistance": 6,
            "attributes": {"l36structure": True}}
    block("l36-airportdoor", [("part", ["lower", "upper"]), ("side", SIDES)], lambda v: airportdoor(v["part"]),
          "Level 36's way in and out (links): a glazed aluminium door flush in a full block of wall (dark steel on five faces, the door "
          "on <side>), in the baggage wall and in walls of the city and the Suburbs, under the airplane sign. Structure; a threshold "
          "(kind l36-airport, ThresholdNetwork.L36.cs)",
          boxes=[(0, 0, 0, 1, 1, 1)], material="Metal", sounds=METAL,
          data=dict(door, behaviors=[{"name": "BackroomsThreshold", "properties": {"kind": "l36-airport"}}]))
    block("l36-airportsign", [("side", SIDES)], lambda v: airportsign(),
          "Level 36's way in and out (links): the backlit sign over the door, a full block of wall with the airplane on a yellow tile "
          "and an arrow down on <side>. Structure",
          boxes=[(0, 0, 0, 1, 1, 1)], material="Metal", sounds=METAL, data=dict(door, lightHsv=[8, 4, 6]))
    block("l36-sink", [("state", ["dry", "overflow"]), ("side", SIDES)], lambda v: sink(v["state"]),
          "Level 36's restrooms (links): a washbasin on its vanity, against the wall behind it; overflow it (use) and hold your head "
          "under (hold use) for the Poolrooms (Fandom). Structure; BackroomsL36Sink",
          boxes=[(0, 0, 3 / 16, 1, 1, 1)], material="Ceramic", sounds=CERAMIC,
          data={"behaviors": [{"name": "BackroomsL36Sink"}], "attributes": {"l36structure": True}})


# ======================================================================== Checks and main

def check():
    problems = []
    tex_dir = TX.TEX
    for name in SHAPE_FILES:
        data = json.load(open(os.path.join(SHAPES, name + ".json"), encoding="utf-8"))
        used = {f["texture"][1:] for e in data["elements"] for f in e["faces"].values()}
        for k in used:
            if k not in data["textures"]:
                problems.append(f"{name}: #{k} undefined")
            elif not os.path.exists(os.path.join(tex_dir, k + ".png")):
                problems.append(f"{name}: texture {k} missing")
    for code in CODES:
        raw = open(os.path.join(BLOCKS, code + ".json"), encoding="utf-8").read()
        json.loads(re.sub(r"^//.*$", "", raw, flags=re.M))
    for p in problems:
        print("CHECK:", p)
    return not problems


def main():
    CODES.clear()
    SHAPE_FILES.clear()
    written = TX.textures()
    checkin()
    seats()
    gatedesks()
    gatedoors()
    stanchions()
    scanners()
    xrays()
    tray_stack()
    booths()
    perfumes()
    meal_tables()
    meetings()
    cabin_seats()
    lost_founds()
    link_blocks()
    ok = check()
    print(f"gen_36_props: {len(CODES)} block types, {len(SHAPE_FILES)} shapes, {len(written)} textures, {'ok' if ok else 'PROBLEMS'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
