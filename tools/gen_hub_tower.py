"""The Hub's Tower and outposts (for tools/gen_hub.py): ashlar, pilasters, arches, cornice, marble, stairs,
balustrades, the headless statue, the artifacts under glass, the dusk light; the M.E.G. outpost's doormat, banner,
key cabinet, door register and field radio; Camp Amber's sign and the camp cot.

Wall-hung pieces sit in the air cell in front of a wall, their back against the wall to the south (z = 16).
"""
import math

from gen_hub_kit import (CLOTH, DIRS, FRONT, GLASS, METAL, ROTATE, SIDES, STONE, WOOD, block, boxes_by_side, bx,
                         cube_family, cuboid, mirror_x, name, oriented, shape)


def stone_blocks():
    cube_family("hub-ashlar", {"plain": "Ashlar", "worn": "Worn Ashlar"}, ["plain", "worn"], lambda k: "ashlar-" + k,
                "The Tower's walls: pale limestone ashlar, two courses to a block", resistance=8)
    cube_family("hub-marble", {"plain": "Polished Marble", "inlay": "Inlaid Marble", "centre": "Marble Medallion"},
                ["plain", "inlay", "centre"], lambda k: "marble-" + k,
                "The rotunda and Approach floors: polished marble; a dark inlaid band (for the inlaid circle; its band runs"
                " west-east); the medallion at the very centre", turned=("plain",), resistance=8)

    # Pilaster: a fluted half-column 5 units proud of the wall to the south (base, shaft, capital)
    def flutes(y1, y2):
        els = [bx("Core", (3.5, y1, 11.5), (12.5, y2, 16), "flute", faces=("north", "east", "west"))]
        for i in range(6):
            x = 3.5 + i * 1.8
            els.append(bx(f"Fillet{i}", (x - 0.35, y1, 11), (x + 0.35, y2, 11.5), "ashlar-plain", faces=("north", "east", "west")))
        els.append(bx("EdgeL", (3, y1, 12), (3.5, y2, 16), "ashlar-plain", faces=("north", "west")))
        els.append(bx("EdgeR", (12.5, y1, 12), (13, y2, 16), "ashlar-plain", faces=("north", "east")))
        return els
    base = [bx("Plinth", (1.5, 0, 9.5), (14.5, 2.5, 16), "ashlar-plain", faces=FRONT),
            bx("Torus", (2, 2.5, 10), (14, 4.5, 16), "ashlar-plain", faces=FRONT),
            bx("TorusRound", (2.4, 2.1, 9.6), (13.6, 4.9, 16), "ashlar-plain", faces=("north", "east", "west")),
            bx("Scotia", (2.8, 4.5, 10.8), (13.2, 5.2, 16), "ashlar-plain", faces=FRONT),
            bx("TorusUpper", (2.4, 5.2, 10.4), (13.6, 6.4, 16), "ashlar-plain", faces=FRONT)] + flutes(6.4, 16)
    capital = flutes(0, 7) + [
        bx("Necking", (2.6, 7, 10.6), (13.4, 8, 16), "ashlar-plain", faces=FRONT),
        bx("Echinus1", (2.2, 8, 10.2), (13.8, 9.5, 16), "ashlar-plain", faces=FRONT),
        bx("Echinus2", (1.6, 9.5, 9.6), (14.4, 11, 16), "ashlar-plain", faces=FRONT),
        bx("Echinus3", (1.2, 11, 9.2), (14.8, 12, 16), "ashlar-plain", faces=FRONT),
        bx("Abacus", (0.6, 12, 8.6), (15.4, 15, 16), "ashlar-plain", faces=FRONT),
        bx("AbacusLip", (0.4, 15, 8.4), (15.6, 16, 16), "ashlar-plain", faces=FRONT)]
    oriented("hub-pilaster", "Pilaster", {"base": shape("pilaster-base", base), "shaft": shape("pilaster-shaft", flutes(0, 16)),
                                          "capital": shape("pilaster-capital", capital)},
             "A fluted half-column standing out from the Tower's wall (to its south): base, shaft, capital; every 36 degrees"
             " round the rotunda", groups=[("part", ["base", "shaft", "capital"])], box=(0.06, 0, 0.55, 0.94, 1, 1),
             extra={"resistance": 8, "drops": []}, creative="construction")

    # Arch: the top row of a 3-wide opening made into a segmental arch: the stone above the curve, voussoirs and a
    # keystone standing 2 units proud. Parts left / key / right as the viewer sees them.
    R0, CY = 30.0, -18.0  # the intrados: a circle through the springings (u = 0, 48 at the block's bottom) and 12 up at the crown

    def arch(part):
        off = {"left": 0, "key": 16, "right": 32}[part]
        els = []
        for i in range(16):
            u = off + i + 0.5
            y = CY + math.sqrt(R0 * R0 - (u - 24) ** 2)
            y = max(0.0, min(16.0, round(y * 2) / 2))
            if y < 16:
                x = 16 - (i + 1)
                els.append(bx(f"Soffit{i}", (x, y, 0), (x + 1, 16, 16), "ashlar-plain", faces=("north", "down", "south")))
        # Voussoirs: wedges round the arc, each a box turned to its angle
        for k in range(-4, 5):
            a = k * 11.0
            if k == 0:
                if part != "key":
                    continue
                rin, rout, half, dz = R0 - 0.5, R0 + 6.5, 2.4, -3.0
            else:
                rin, rout, half, dz = R0, R0 + 4.5, 2.0, -2.0
            cu = 24 + (rin + rout) / 2 * math.sin(math.radians(a))
            cyv = CY + (rin + rout) / 2 * math.cos(math.radians(a))
            if not off <= cu < off + 16:
                continue
            x = 16 - (cu - off)
            h = (rout - rin) / 2
            els.append(bx(f"Voussoir{k + 4}", (x - half, cyv - h, dz), (x + half, cyv + h, 0), "ashlar-plain", faces=FRONT,
                          rot=(0, 0, a), origin=(x, cyv, 0)))
        return els
    oriented("hub-arch", "Stone Arch", {p: shape(f"arch-{p}", arch(p)) for p in ("left", "key", "right")},
             "The arch over each of the Tower's ten passages: the top row of a 3-wide opening (left, key, right as the viewer"
             " sees them, face to the north), stone above a segmental curve with voussoirs and a keystone",
             groups=[("part", ["left", "key", "right"])], box=(0, 0.25, 0, 1, 1, 1), extra={"resistance": 8, "drops": []},
             creative="construction")

    # Cornice: an ogee moulding running round the top of the rotunda, standing out from the wall to the south; the
    # dusk light hides behind it
    cornice = [bx("Fillet", (0, 4, 14), (16, 5.5, 16), "ashlar-plain", faces=FRONT),
               bx("Cyma1", (0, 5.5, 13), (16, 7, 16), "ashlar-plain", faces=FRONT),
               bx("Cyma2", (0, 7, 12), (16, 8.5, 16), "ashlar-plain", faces=FRONT),
               bx("Cyma3", (0, 8.5, 11.2), (16, 10, 16), "ashlar-plain", faces=FRONT),
               bx("Cyma4", (0, 10, 10.6), (16, 11.5, 16), "ashlar-plain", faces=FRONT),
               bx("Corona", (0, 11.5, 9.6), (16, 14.5, 16), "ashlar-plain", faces=FRONT),
               bx("Cap", (0, 14.5, 9.2), (16, 15.2, 16), "ashlar-plain", faces=FRONT)]
    for i in range(4):  # dentils under the corona
        x = 1 + i * 4
        cornice.append(bx(f"Dentil{i}", (x, 10.2, 10.2), (x + 2, 11.5, 10.6), "ashlar-plain", faces=FRONT))
    oriented("hub-cornice", "Cornice", {None: shape("cornice", cornice)},
             "The ogee cornice round the top of the rotunda, standing out from the wall to its south; the dusk light hides"
             " behind it", box=(0, 0.25, 0.55, 1, 1, 1), extra={"resistance": 8, "drops": []}, creative="construction")

    # Marble stairs: -north climbs toward the north (its high step on the north half), as vanilla's
    stairs = [bx("Low", (0, 0, 0), (16, 8, 16), "marble-plain"), bx("High", (0, 8, 0), (16, 16, 8), "marble-plain"),
              bx("NosingLow", (0, 7.4, 15.6), (16, 8, 16.4), "marble-plain"), bx("NosingHigh", (0, 15.4, 7.6), (16, 16, 8.4), "marble-plain")]
    path = shape("marblestairs", stairs)
    block("hub-marblestairs", {
        "variantgroups": [{"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-north"], "construction": ["*-north"]}, "blockmaterial": "Stone", "drawtype": "json",
        "shapeByType": {f"*-{s}": {"base": path, "rotateY": ROTATE[s]} for s in SIDES},
        "collisionSelectionBoxesByType": {f"*-{s}": [cuboid((0, 0, 0, 1, 0.5, 1)), cuboid((0, 0.5, 0, 1, 1, 0.5), s)] for s in SIDES},
        "sidesolid": {"all": False, "down": True}, "sideopaque": {"all": False, "down": True}, "lightAbsorption": 0,
        "resistance": 8, "sounds": STONE, "drops": []},
          "The Tower's spiral stair: polished marble steps. -north climbs toward the north (the high step on its north half)")
    name("hub-marblestairs-*", "Marble Stairs")

    # Balustrade: a plinth, three turned balusters and a handrail, running west-east across the middle of the block
    bal = [bx("Plinth", (0, 0, 5), (16, 2, 11), "marble-plain"), bx("PlinthLip", (0, 2, 5.5), (16, 2.6, 10.5), "marble-plain")]
    for i, x in enumerate((2.7, 8, 13.3)):
        for j, (y1, y2, r) in enumerate(((2.6, 4, 1.6), (4, 5, 1.1), (5, 8.5, 1.8), (8.5, 10.5, 1.2), (10.5, 11.5, 0.8), (11.5, 12.6, 1.3))):
            bal.append(bx(f"Baluster{i}{j}", (x - r, y1, 8 - r), (x + r, y2, 8 + r), "marble-plain"))
    bal += [bx("Rail", (0, 12.6, 5.6), (16, 14.6, 10.4), "marble-plain"), bx("RailCap", (0, 14.6, 5), (16, 15.6, 11), "marble-plain")]
    oriented("hub-balustrade", "Marble Balustrade", {None: shape("balustrade", bal)},
             "A marble balustrade for the stair's galleries and the balcony: a rail on three turned balusters, running"
             " west-east through the middle of the -north block (north-south when turned east or west)",
             box=(0, 0, 0.3, 1, 1, 0.7), extra={"resistance": 8, "drops": [], "collisionboxByType": boxes_by_side((0, 0, 0.3, 1, 1.5, 0.7))},
             creative="construction")

    # The dusk: an invisible light behind the cornice
    block("hub-dusklight", {"creativeinventory": {"general": ["*"]}, "blockmaterial": "Stone", "drawtype": "Empty",
                            "sidesolid": {"all": False}, "sideopaque": {"all": False}, "collisionbox": None, "selectionbox": None,
                            "lightAbsorption": 0, "lightHsv": [2, 4, 13], "resistance": 999, "drops": [], "replaceable": 10},
          "Invisible: the perpetual dusk that lights the Tower from behind its cornice")
    name("hub-dusklight", "Dusk")


def statue():
    """The headless statue: a draped figure in contrapposto on a moulded plinth, its head long gone, one forearm broken
    away. The anchor block is the plinth; the figure rises 2 more blocks (put hub-statuefill in them for collision)."""
    m = "statue"
    els = [bx("PlinthBase", (0.5, 0, 0.5), (15.5, 2, 15.5), m), bx("PlinthDie", (1.5, 2, 1.5), (14.5, 11, 14.5), m),
           bx("PlinthCap", (0.8, 11, 0.8), (15.2, 13, 15.2), m), bx("PlinthTop", (1.2, 13, 1.2), (14.8, 14, 14.8), m)]
    # Feet and the hem of the robe
    els += [bx("FootL", (8.5, 14, 3.2), (11, 15.5, 7), m), bx("FootR", (5, 14, 3.8), (7.5, 15.2, 7.2), m),
            bx("Hem", (3.6, 14, 5.5), (12.4, 17, 11.5), m)]
    # Skirt of the robe, narrowing to the hips, in folds
    for i, (y1, y2, w, d) in enumerate(((17, 22, 4.2, 3.0), (22, 27, 3.9, 2.8), (27, 32, 3.6, 2.6), (32, 36, 3.5, 2.6))):
        els.append(bx(f"Skirt{i}", (8 - w, y1, 8.5 - d), (8 + w, y2, 8.5 + d), m))
    for i, x in enumerate((4.8, 6.6, 8.4, 10.2)):
        els.append(bx(f"Fold{i}", (x, 15, 5.2 - 0.2 * (i % 2)), (x + 0.9, 33 - 2 * (i % 2), 5.9), m, rot=(0, 0, -2 + i), origin=(x, 15, 5.5)))
    # The weight-bearing leg showing through the cloth, the other knee forward
    els.append(bx("KneeR", (5.2, 24, 4.6), (7.6, 28, 6.0), m))
    # Torso, turned a little against the hips (contrapposto)
    torso = [bx("Waist", (5, 36, 6.2), (11, 39, 10.8), m), bx("Chest", (4.4, 39, 5.8), (11.6, 44, 11.2), m),
             bx("Shoulders", (3.4, 43.5, 6.3), (12.6, 46, 10.7), m), bx("Breast", (5, 40, 5.4), (11, 43, 6), m),
             bx("Sash", (4.2, 37.5, 5.6), (11.8, 39, 11.4), m, rot=(0, 0, 18), origin=(8, 38, 8.5)),
             bx("NeckStump", (6.8, 46, 7.4), (9.2, 47.4, 9.6), m), bx("Break1", (7.2, 47.4, 7.8), (8.6, 48.1, 9.2), m),
             bx("Break2", (7.0, 47.4, 8.6), (7.8, 48.5, 9.4), m)]
    for e in torso:
        e.setdefault("rotationOrigin", [8, 36, 8.5])
        e["rotationY"] = e.get("rotationY", 0) + 8
    els += torso
    # Right arm (viewer's left) hanging, the hand holding the drape; the left arm broken off above the elbow
    els += [bx("ArmRUpper", (11.6, 37, 7.2), (13.6, 45.5, 9.6), m, rot=(0, 0, 6), origin=(12.6, 45.5, 8.4)),
            bx("ArmRLower", (12.2, 30.5, 7.0), (14.0, 37.5, 9.4), m, rot=(0, 0, 2), origin=(13, 37.5, 8.2)),
            bx("HandR", (12.0, 28.4, 6.8), (14.2, 30.8, 9.4), m),
            bx("ArmLStump", (2.2, 40, 6.8), (4.4, 45.5, 9.8), m, rot=(0, 0, -14), origin=(3.3, 45.5, 8.3)),
            bx("ArmLBreak", (1.3, 39.0, 7.3), (3.4, 40.5, 9.3), m, rot=(0, 0, -14), origin=(3.3, 45.5, 8.3))]
    # The drape over the left shoulder, falling behind
    els += [bx("Drape", (3, 33, 9.6), (7.2, 46.2, 11.6), m, rot=(0, 0, -8), origin=(5, 46, 10.6)),
            bx("DrapeFall", (2.6, 20, 10.2), (6, 33.5, 11.8), m)]
    path = shape("statue", els)
    block("hub-statue", {"creativeinventory": {"general": ["*"], "decorative": ["*"]}, "blockmaterial": "Stone",
                         "drawtype": "json", "shape": {"base": path}, "sidesolid": {"all": False}, "sideopaque": {"all": False},
                         "lightAbsorption": 0, "resistance": 30, "drops": [], "sounds": STONE,
                         "collisionbox": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 1, "z2": 1}},
          "The headless marble statue at the heart of the Tower: this is its plinth; the figure rises two more blocks, which"
          " take hub-statuefill for collision. Faces north")
    name("hub-statue", "Headless Statue")
    block("hub-statuefill", {"creativeinventory": {"general": ["*"]}, "blockmaterial": "Stone", "drawtype": "Empty",
                             "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0,
                             "collisionbox": {"x1": 0.2, "y1": 0, "z1": 0.25, "x2": 0.8, "y2": 1, "z2": 0.75},
                             "selectionbox": {"x1": 0.2, "y1": 0, "z1": 0.25, "x2": 0.8, "y2": 1, "z2": 0.75},
                             "resistance": 30, "drops": [], "sounds": STONE},
          "Invisible: the statue's body above its plinth, so nobody walks through it")
    name("hub-statuefill", "Headless Statue")


def pedestals():
    """A marble pedestal with an artifact under a glass bell (the bell reaches into the block above)."""
    stand = [bx("Foot", (2.5, 0, 2.5), (13.5, 1.5, 13.5), "marble-plain"), bx("Die", (3.5, 1.5, 3.5), (12.5, 10.5, 12.5), "marble-plain"),
             bx("Cap", (2.8, 10.5, 2.8), (13.2, 12, 13.2), "marble-plain"), bx("Cushion", (4.5, 12, 4.5), (11.5, 12.6, 11.5), "velvetred")]
    bell = [bx("BellN", (4, 12, 4), (12, 21, 4.2), "bellglass", faces=("north", "south"), full=True),
            bx("BellS", (4, 12, 11.8), (12, 21, 12), "bellglass", faces=("north", "south"), full=True),
            bx("BellW", (4, 12, 4.2), (4.2, 21, 11.8), "bellglass", faces=("east", "west"), full=True),
            bx("BellE", (11.8, 12, 4.2), (12, 21, 11.8), "bellglass", faces=("east", "west"), full=True),
            bx("BellTop", (4, 21, 4), (12, 21.2, 12), "bellglass", faces=("up", "down"), full=True),
            bx("BellKnob", (7.2, 21.2, 7.2), (8.8, 22.2, 8.8), "brass"),
            bx("BellRim", (3.8, 12, 3.8), (12.2, 12.4, 12.2), "brass")]
    y = 12.6
    art = {
        # A Scaraback: a beetle the size of a fist, its shell split down the back
        "scaraback": [bx("Shell", (6, y + 0.6, 5.5), (10, y + 2.6, 10), "scarabshell"), bx("Head", (6.8, y + 0.6, 4.4), (9.2, y + 1.8, 5.5), "scarab"),
                      bx("Horn", (7.6, y + 1.4, 3.6), (8.4, y + 2.0, 4.6), "scarab")]
                     + [bx(f"Leg{i}", (5.3 if i % 2 else 9.8, y, 5.8 + (i // 2) * 1.5), (6.2 if i % 2 else 10.7, y + 1, 6.3 + (i // 2) * 1.5), "scarab") for i in range(6)],
        # The small squid-like thing in a jar, as the Tower's museum keeps it
        "squidjar": [bx("Liquid", (5.5, y, 5.5), (10.5, y + 6, 10.5), "jarliquid", full=True),
                     bx("Lid", (5.2, y + 6, 5.2), (10.8, y + 7, 10.8), "brass"),
                     bx("Mantle", (7, y + 2.6, 7), (9, y + 5.2, 9), "squid"),
                     bx("Eye", (6.9, y + 2.8, 7.4), (7.1, y + 3.2, 7.9), "keyhole")]
                    + [bx(f"Arm{i}", (7.2 + (i % 3) * 0.6, y + 0.4, 7.2 + (i // 3) * 1.2), (7.6 + (i % 3) * 0.6, y + 2.8, 7.6 + (i // 3) * 1.2), "squid") for i in range(6)],
        # A pool noodle from Level 37, coiled
        "noodle": [bx("N1", (5, y, 5), (11, y + 1.5, 6.5), "noodle"), bx("N2", (9.5, y, 6.5), (11, y + 1.5, 11), "noodle"),
                   bx("N3", (5, y, 9.5), (9.5, y + 1.5, 11), "noodle"), bx("N4", (5, y + 1.5, 6.5), (6.5, y + 3, 9.5), "noodle")],
        # A stop-motion clay figure from Level 94: a round head, button eyes, a blob of a body
        "clayfigure": [bx("Body", (6.5, y, 7), (9.5, y + 3.5, 9.5), "clayblue"), bx("Head", (6.6, y + 3.5, 6.8), (9.4, y + 6.2, 9.6), "clay"),
                       bx("EyeL", (7.2, y + 4.6, 6.6), (7.9, y + 5.4, 6.8), "keyhole"), bx("EyeR", (8.1, y + 4.6, 6.6), (8.8, y + 5.4, 6.8), "keyhole"),
                       bx("ArmL", (5.6, y + 1.4, 7.6), (6.5, y + 3.2, 8.6), "clayblue"), bx("ArmR", (9.5, y + 1.4, 7.6), (10.4, y + 3.2, 8.6), "clayblue")],
        # An old radio
        "radio": [bx("Cabinet", (5, y, 6), (11, y + 5, 10), "radiowood"), bx("Grille", (5.6, y + 1.8, 5.9), (10.4, y + 4.4, 6), "radiogrille", faces=("north",), full=True),
                  bx("Dial", (6.2, y + 0.5, 5.8), (7.4, y + 1.5, 6), "brass"), bx("Knob", (8.8, y + 0.5, 5.8), (9.8, y + 1.5, 6), "brass"),
                  bx("Arch", (5.6, y + 5, 6.4), (10.4, y + 5.8, 9.6), "radiowood")],
        # A shard of the King's crown from Level 94
        "crownshard": [bx("Band", (5.5, y, 7.4), (10.5, y + 1.5, 8.6), "crowngold"), bx("Point1", (6, y + 1.5, 7.6), (7.2, y + 3.6, 8.4), "crowngold"),
                       bx("Point2", (8.2, y + 1.5, 7.6), (9.4, y + 4.4, 8.4), "crowngold"), bx("Jewel", (8.4, y + 0.4, 7.2), (9.2, y + 1.2, 7.4), "velvetred")],
        # A Level Key on the cushion
        "levelkey": [bx("Bow", (5.4, y, 7), (8, y + 0.6, 9.6), "brass"), bx("Shank", (8, y, 7.9), (11.4, y + 0.6, 8.7), "brass"),
                     bx("Bit", (10.2, y, 8.7), (11.4, y + 0.6, 9.8), "brass"), bx("BowHole", (6.2, y + 0.6, 7.8), (7.2, y + 0.65, 8.8), "keyhole", faces=("up",))],
        # An M.E.G. badge on a little stand
        "megbadge": [bx("Stand", (7.2, y, 7.6), (8.8, y + 1, 9.2), "brass"), bx("Shield", (5.6, y + 1, 7.8), (10.4, y + 6, 8.4), "megnavy"),
                     bx("Rim", (5.4, y + 0.8, 8.4), (10.6, y + 6.2, 8.8), "silver"), bx("Star", (7.4, y + 2.8, 7.6), (8.6, y + 4, 7.8), "silver")],
    }
    shapes = {k: shape(f"pedestal-{k}", stand + v + bell) for k, v in art.items()}
    block("hub-pedestal", {
        "variantgroups": [{"code": "artifact", "states": list(art)}],
        "creativeinventory": {"general": ["*"], "decorative": ["*"]}, "blockmaterial": "Stone", "drawtype": "json",
        "renderpass": "Transparent", "shapeByType": {f"*-{k}": {"base": p} for k, p in shapes.items()},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 3, "drops": [],
        "sounds": GLASS, "collisionbox": cuboid((0.16, 0, 0.16, 0.84, 1, 0.84)), "selectionbox": cuboid((0.16, 0, 0.16, 0.84, 1.4, 0.84))},
          "The Tower's museum rows: an artifact under a glass bell on a marble pedestal. Breaking one brings the Keymaster")
    for k, eng in (("scaraback", "Scaraback"), ("squidjar", "Specimen Jar"), ("noodle", "Pool Noodle"), ("clayfigure", "Clay Figure"),
                   ("radio", "Old Radio"), ("crownshard", "Crown Shard"), ("levelkey", "Level Key"), ("megbadge", "M.E.G. Badge")):
        name(f"hub-pedestal-{k}", f"{eng} under Glass")


def outpost():
    # Doorstep Carpet: the doormat in front of the outpost's door
    mat = [bx("Mat", (1, 0, 3), (15, 0.8, 13), "doormat", faces=("up",), full=True),
           bx("MatSides", (1, 0, 3), (15, 0.8, 13), "coir", faces=("north", "east", "south", "west", "down"))]
    oriented("hub-doormat", "Doorstep Carpet", {None: shape("doormat", mat)},
             "The M.E.G. outpost's worn coir doormat, 'Doorstep Carpet', in front of its door (WELCOME reads from the north)",
             material="Cloth", sounds=CLOTH, box=(0.06, 0, 0.19, 0.94, 0.05, 0.81), collide=False,
             extra={"drops": [{"type": "item", "code": "carpetfibre", "quantity": {"avg": 2, "var": 1}}]})

    # The M.E.G. banner hanging from a rod on the wall to the south
    banner = [bx("Rod", (0.5, 15, 13.4), (15.5, 15.8, 14.2), "rod"), bx("BracketL", (1, 14.6, 14.2), (2, 16, 16), "rod"),
              bx("BracketR", (14, 14.6, 14.2), (15, 16, 16), "rod")]
    # The cloth sags a little from the rod: two panels, the lower tipped out
    banner += [bx("ClothTop", (1.5, 6, 13.5), (14.5, 15, 14), "megbanner", faces=("north",), uv=[0, 0, 16, 10.7]),
               bx("ClothTopBack", (1.5, 6, 13.5), (14.5, 15, 14), "megnavy", faces=("south", "east", "west", "up", "down")),
               bx("ClothLow", (1.5, -9, 13.1), (14.5, 6, 13.6), "megbanner", faces=("north",), uv=[0, 10.7, 16, 16],
                  rot=(4, 0, 0), origin=(8, 6, 13.5)),
               bx("ClothLowBack", (1.5, -9, 13.1), (14.5, 6, 13.6), "megnavy", faces=("south", "east", "west", "down"),
                  rot=(4, 0, 0), origin=(8, 6, 13.5))]
    oriented("hub-megbanner", "M.E.G. Banner", {None: shape("megbanner", banner)},
             "The M.E.G.'s navy banner with its white eagle, hanging from a rod on the wall to the south; it hangs a block"
             " and a half, into the block below", material="Cloth", sounds=CLOTH, box=(0.06, 0, 0.8, 0.94, 1, 1), collide=False,
             extra={"drops": [{"type": "item", "code": "game:cloth-plain", "quantity": {"avg": 1, "var": 0}}]})

    # Key cabinet: a steel wall cabinet with a mesh door, twelve keys on hooks inside
    cab = [bx("Back", (1, 1, 15), (15, 15, 16), "cabinetback", faces=("north",)),
           bx("Top", (1, 14, 10.5), (15, 15, 16), "cabinet"), bx("Bottom", (1, 1, 10.5), (15, 2, 16), "cabinet"),
           bx("SideL", (14, 2, 10.5), (15, 14, 16), "cabinet"), bx("SideR", (1, 2, 10.5), (2, 14, 16), "cabinet"),
           bx("Mesh", (2, 2, 10.8), (14, 14, 11), "mesh", faces=("north", "south"), full=True),
           bx("DoorFrameT", (1.5, 13.4, 10.2), (14.5, 14, 10.8), "cabinet"), bx("DoorFrameB", (1.5, 2, 10.2), (14.5, 2.6, 10.8), "cabinet"),
           bx("DoorFrameL", (13.9, 2.6, 10.2), (14.5, 13.4, 10.8), "cabinet"), bx("DoorFrameR", (1.5, 2.6, 10.2), (2.1, 13.4, 10.8), "cabinet"),
           bx("Hasp", (2.2, 7, 9.6), (3.2, 9, 10.2), "brass"), bx("Padlock", (2.0, 5.4, 9.4), (3.4, 7, 10.0), "brass")]
    for r in range(3):
        for c in range(4):
            x, yy = 3.4 + c * 3, 11.6 - r * 3.6
            brass = (r + c) % 3 != 0
            cab += [bx(f"Hook{r}{c}", (x + 0.6, yy, 13.8), (x + 1, yy + 0.4, 15), "silver"),
                    bx(f"Key{r}{c}", (x + 0.4, yy - 2.2, 13.9), (x + 1.2, yy, 14.2), "brass" if brass else "ironkey"),
                    bx(f"KeyBow{r}{c}", (x + 0.1, yy - 0.3, 13.85), (x + 1.5, yy + 0.6, 14.25), "brass" if brass else "ironkey")]
    oriented("hub-keycabinet", "Key Cabinet", {None: shape("keycabinet", cab)},
             "The M.E.G. outpost's locked key cabinet on the wall to the south: a mesh door, twelve keys on hooks (decor; the"
             " keys are not for the taking)", material="Metal", sounds=METAL, box=(0.06, 0.06, 0.62, 0.94, 0.94, 1),
             extra={"resistance": 20, "drops": []})

    # The door register: a whiteboard on a wheeled stand (the board rises above its block)
    wb = [bx("Board", (0.5, 10, 7.4), (15.5, 22, 8.2), "whiteboard", faces=("north",), full=True),
          bx("BoardBack", (0.5, 10, 7.4), (15.5, 22, 8.2), "aluminium", faces=("south", "east", "west", "up", "down")),
          bx("Tray", (3, 9.4, 6.4), (13, 10, 8.2), "aluminium"),
          bx("PostL", (14.6, 1, 7.5), (15.4, 21, 8.3), "aluminium"), bx("PostR", (0.6, 1, 7.5), (1.4, 21, 8.3), "aluminium"),
          bx("FootL", (14.3, 0, 3), (15.7, 1, 13), "aluminium"), bx("FootR", (0.3, 0, 3), (1.7, 1, 13), "aluminium"),
          bx("Marker", (4, 10, 6.8), (6.5, 10.6, 7.4), "ribbon"), bx("Marker2", (7, 10, 6.8), (9.5, 10.6, 7.4), "megnavy")]
    oriented("hub-whiteboard", "Door Register", {None: shape("whiteboard", wb)},
             "The M.E.G.'s door register: a whiteboard on a stand, the Hub sketched on it in marker, facing north. Right-click"
             " it to have the open doors and the Tower marked on your map", material="Metal", sounds=METAL,
             box=(0, 0, 0.2, 1, 1, 0.8), extra={"resistance": 20, "drops": []})

    radio = [bx("Case", (3, 0, 5), (13, 7, 11), "olive"), bx("Face", (3, 0, 5), (13, 7, 11), "radioface", faces=("north",), full=True),
             bx("Handle", (5, 7, 7.5), (11, 7.6, 8.5), "blackknob"), bx("HandleL", (5, 7, 7.5), (5.6, 8.6, 8.5), "blackknob"),
             bx("HandleR", (10.4, 7, 7.5), (11, 8.6, 8.5), "blackknob"), bx("HandleTop", (5, 8.6, 7.5), (11, 9.2, 8.5), "blackknob"),
             bx("Antenna", (11.8, 7, 9.6), (12.2, 19, 10), "blackknob", rot=(0, 0, -12), origin=(12, 7, 9.8)),
             bx("KnobA", (4.2, 1.6, 4.4), (5.6, 3, 5), "blackknob"), bx("KnobB", (7.2, 1.6, 4.4), (8.6, 3, 5), "blackknob"),
             bx("Handset", (13, 0, 6), (15.5, 2, 10), "blackknob")]
    oriented("hub-fieldradio", "Field Radio", {None: shape("fieldradio", radio)},
             "An olive-drab field radio, playing nothing", material="Metal", sounds=METAL, box=(0.18, 0, 0.3, 0.97, 0.6, 0.7),
             extra={"drops": [{"type": "item", "code": "scrapwire", "quantity": {"avg": 1.5, "var": 0.5}},
                              {"type": "item", "code": "metalbracket", "quantity": {"avg": 0.5, "var": 0}}]})

    sign = [bx("Board", (1, 7, 7.2), (15, 21, 8.2), "ambersign", faces=("north",), full=True),
            bx("BoardBack", (1, 7, 7.2), (15, 21, 8.2), "plywood", faces=("south", "east", "west", "up", "down")),
            bx("LegL", (13, 0, 8.2), (14.4, 19, 9.4), "plywood", rot=(-8, 0, 0), origin=(13.7, 19, 8.8)),
            bx("LegR", (1.6, 0, 8.2), (3, 19, 9.4), "plywood", rot=(-8, 0, 0), origin=(2.3, 19, 8.8)),
            bx("Prop", (7.3, 0, 12), (8.7, 18, 13.2), "plywood", rot=(20, 0, 0), origin=(8, 18, 9))]
    oriented("hub-ambersign", "Camp Amber Sign", {None: shape("ambersign", sign)},
             "Camp Amber's painted board: CAMP AMBER - NEW? ASK US, facing north", material="Wood", sounds=WOOD,
             box=(0.06, 0, 0.3, 0.94, 1, 0.85), extra={"drops": [{"type": "item", "code": "game:plank-aged", "quantity": {"avg": 2, "var": 1}}]})

    # A folding camp cot, two blocks long: head and foot halves (the head toward the north)
    def cot(part):
        els = [bx("Canvas", (2.5, 5.5, 0), (13.5, 6.2, 16), "canvas"),
               bx("RailL", (13.5, 5, 0), (14.3, 6.4, 16), "rod"), bx("RailR", (1.7, 5, 0), (2.5, 6.4, 16), "rod")]
        endz = (0, 0.8) if part == "head" else (15.2, 16)
        els.append(bx("End", (1.7, 5, endz[0]), (14.3, 6.4, endz[1]), "rod"))
        lz = 2 if part == "head" else 14
        els += [bx("LegA", (2, 0, lz - 0.4), (2.8, 5, lz + 0.4), "rod", rot=(0, 0, 18), origin=(2.4, 5, lz)),
                bx("LegB", (13.2, 0, lz - 0.4), (14, 5, lz + 0.4), "rod", rot=(0, 0, -18), origin=(13.6, 5, lz)),
                bx("Cross", (2.4, 1.5, lz - 0.3), (13.6, 2.1, lz + 0.3), "rod")]
        if part == "head":
            els.append(bx("Blanket", (3, 6.2, 9), (13, 7.2, 16), "megnavy"))
        else:
            els.append(bx("Blanket", (3, 6.2, 0), (13, 7.2, 10), "megnavy"))
        return els
    oriented("hub-cot", "Camp Cot", {p: shape(f"cot-{p}", cot(p)) for p in ("head", "foot")},
             "A folding camp cot at the M.E.G. outpost, two blocks long: the head half and the foot half (the head toward the"
             " north in the -north variant, so the foot is the block to its south)", groups=[("part", ["head", "foot"])],
             material="Cloth", sounds=CLOTH, box=(0.06, 0, 0, 0.94, 0.45, 1),
             extra={"drops": [{"type": "item", "code": "game:cloth-plain", "quantity": {"avg": 1, "var": 0.5}},
                              {"type": "item", "code": "metalbracket", "quantity": {"avg": 0.5, "var": 0.5}}]})


def generate():
    stone_blocks()
    statue()
    pedestals()
    outpost()
