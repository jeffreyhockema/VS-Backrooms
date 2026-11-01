"""Level 14 "The Hospital": the models of the surgery rooms, the torture chambers, the T.14.R.G.'s camp, the
contaminated rooms and the halls (tools/gen_14_props.py). Each function returns elements modelled facing north."""
import math
import random

import modelkit as MK
from gen_14_props_kit import B, no, pic, glow, turned, transparent, rename, octagon, rod, mirror_x, move, turn, clip_z
from gen_14_props_a import castor, glass_cabinet, five_star, WORK


# ======================================================================== Surgery

def optable_model():
    """An operating table 32 long (foot z 0-16, head z 16-32) on a single column, its top tilted head-down 15 degrees
    about the column's head: a heavy base, an octagonal column, a steel frame with side rails, black-green pads cracked
    and stained, a strap over the chest and one over the shins, a drape slid half off."""
    S = "p-steel"
    els = [B("Base", (3, 0, 11), (13, 1.5, 27), {"top": "p-whiteworn", "side": "p-whiteworn"}),
           B("BasePlinth", (3.5, 0, 10.5), (12.5, 0.75, 27.5), "p-darksteel", faces=no("down", "up"))]
    els += octagon("Column", 8, 19, 2, 1.5, 9.5, "p-whiteworn")
    els.append(B("Head", (5.5, 9.5, 17), (10.5, 11.5, 21), "p-darksteel"))
    tilt = dict(rx=15, origin=(8, 12, 19))
    top = []
    for part, z1, z2 in (("F", 1, 16), ("H", 16, 28.5)):
        top += [B(f"Frame{part}", (2.75, 11.5, z1), (13.25, 12.5, z2), S),
                B(f"Pad{part}", (3, 12.5, z1 + 0.25), (13, 14, z2 - 0.25), "p-optpad"),
                B(f"RailW{part}", (2, 11, z1 + 0.5), (2.5, 11.75, z2 - 0.5), "p-chrome"),
                B(f"RailE{part}", (13.5, 11, z1 + 0.5), (14, 11.75, z2 - 0.5), "p-chrome")]
    top += [B("HeadFrame", (5, 11.5, 28.5), (11, 12.5, 31.5), S),
            B("HeadPad", (5.25, 12.5, 28.5), (10.75, 13.75, 31.25), "p-optpad"),
            B("StrapH", (2.75, 14, 21), (13.25, 14.35, 22.75), "p-leather"),
            B("StrapF", (2.75, 14, 5), (13.25, 14.35, 6.75), "p-leather"),
            B("BuckleH", (9, 14.35, 20.85), (10.5, 14.6, 22.9), "p-chrome"),
            B("Drape", (3.5, 14, 9), (14.35, 14.3, 15.4), "p-drapestain"),
            B("DrapeHang", (14.05, 7.5, 9), (14.35, 14.3, 15.4), "p-drapestain")]
    els += turned(top, **tilt)
    return els


def optable(part):
    els = optable_model()
    return clip_z(els, 16, 99, -16) if part == "head" else clip_z(els, -99, 16, 0)


def surglamp():
    """A surgical light hanging in the top block of a room: a canopy on the ceiling, a spindle, three arms out from a
    hub, a lamp head at each arm's end, its lens glowing down; a sterile handle at each lens's centre."""
    els = octagon("Canopy", 8, 8, 2.5, 15.25, 16, "p-white")
    els += [B("Spindle", (7.4, 11.5, 7.4), (8.6, 15.25, 8.6), "p-chrome", faces=no("up", "down"))]
    els += octagon("Hub", 8, 8, 1.4, 10, 11.75, "p-white")
    d = 5.0
    for k, a in enumerate((0, 120, 240)):
        els.append(B(f"Arm{k}", (7.5, 10.4, 8 - d - 0.3), (8.5, 11.2, 8), "p-white", rot=(0, a, 0), origin=(8, 10.4, 8)))
        cx, cz = 8 - d * math.sin(math.radians(a)), 8 - d * math.cos(math.radians(a))
        els += [B(f"Drop{k}", (cx - 0.4, 8.6, cz - 0.4), (cx + 0.4, 10.6, cz + 0.4), "p-chrome", faces=no("up", "down")),
                B(f"Yoke{k}", (cx - 0.7, 7.9, cz - 0.7), (cx + 0.7, 8.6, cz + 0.7), "p-white")]
        els += octagon(f"Dome{k}", cx, cz, 2.0, 6.75, 7.9, "p-lamphead")
        els += octagon(f"Lamp{k}", cx, cz, 3.0, 5.0, 6.75, "p-lamphead")
        r = 2.55
        els += [pic(B(f"LensA{k}", (cx - r, 4.8, cz - r), (cx + r, 5.0, cz + r), "p-lamphead", faces=("down",)), "down", "p-lens", glow=255),
                pic(B(f"LensB{k}", (cx - r, 4.85, cz - r), (cx + r, 5.0, cz + r), "p-lamphead", faces=("down",), rot=(0, 45, 0), origin=(cx, 4.85, cz)),
                    "down", "p-lens", glow=255),
                B(f"Grip{k}", (cx - 0.4, 3.5, cz - 0.4), (cx + 0.4, 4.8, cz + 0.4), "p-greyplastic", faces=no("up"))]
    return els


def instruments(prefix, y, rusty=False, seed=0):
    """What lies on an instrument tray at height y: scalpels, syringes, forceps, a kidney dish, a stethoscope."""
    rng = random.Random(seed)
    j = (lambda: rng.uniform(-14, 14)) if rusty else (lambda: rng.uniform(-3, 3))
    blade = "p-blade" if not rusty else "p-ruststeel"
    els = []
    for i, x in enumerate((3, 4.25, 5.5)):
        els += turned([B(f"{prefix}ScalpelH{i}", (x - 0.25, y, 4), (x + 0.25, y + 0.3, 7.25), "p-chrome"),
                       B(f"{prefix}ScalpelB{i}", (x - 0.3, y, 3.1), (x + 0.3, y + 0.25, 4), blade)], ry=j(), origin=(x, y, 5.5))
    for i, x in enumerate((7.5, 9)):
        els += turned([B(f"{prefix}Syr{i}", (x - 0.45, y, 4.5), (x + 0.45, y + 0.9, 8), "p-syringe"),
                       B(f"{prefix}Plunger{i}", (x - 0.2, y + 0.25, 8), (x + 0.2, y + 0.65, 9.5), "p-white"),
                       B(f"{prefix}Thumb{i}", (x - 0.55, y + 0.1, 9.5), (x + 0.55, y + 0.8, 9.8), "p-white"),
                       B(f"{prefix}Needle{i}", (x - 0.1, y + 0.4, 2.75), (x + 0.1, y + 0.5, 4.5), "p-blade")], ry=j() + (25 if rusty and i else 0),
                      origin=(x, y, 6))
    els += turned([B(f"{prefix}ForcepsA", (3, y, 8.5), (3.4, y + 0.3, 12.5), "p-chrome"),
                   B(f"{prefix}ForcepsB", (3.9, y, 8.5), (4.3, y + 0.3, 12.5), "p-chrome"),
                   B(f"{prefix}ForcepsJ", (3, y, 12.25), (4.3, y + 0.3, 12.75), "p-chrome")], ry=8 + j(), origin=(3.6, y, 10.5))
    els += [B(f"{prefix}Dish", (5.5, y, 9), (9, y + 0.75, 12.25), "p-tray"),
            B(f"{prefix}DishIn", (6, y + 0.5, 9.5), (8.5, y + 0.7, 11.75), "p-blood" if rusty else "p-gauze", faces=("up",))]
    # the stethoscope: a coiled tube (a square loop), the chest piece and the ear tubes
    t = "p-black"
    els += [B(f"{prefix}TubeN", (10, y, 7.5), (13.5, y + 0.4, 8), t), B(f"{prefix}TubeS", (10, y, 11.5), (13.5, y + 0.4, 12), t),
            B(f"{prefix}TubeW", (10, y, 8), (10.5, y + 0.4, 11.5), t), B(f"{prefix}TubeE", (13, y, 8), (13.5, y + 0.4, 11.5), t),
            B(f"{prefix}TubeTail", (11.5, y, 3.5), (12, y + 0.4, 7.5), t)]
    els += octagon(f"{prefix}Chest", 11.75, 3.2, 0.9, y, y + 0.5, "p-chrome")
    els += [B(f"{prefix}EarA", (10.5, y, 12), (10.9, y + 0.35, 13.2), "p-chrome"), B(f"{prefix}EarB", (12.6, y, 12), (13, y + 0.35, 13.2), "p-chrome")]
    return els


def trolley(state):
    """A two-tier instrument trolley on castors, a push handle at its east end, its top tray laid with a drape and
    the instruments of an operation, as if in use. rusty: gone to rust, the drape bloodied, the things scattered."""
    rusty = state == "rusty"
    frame = "p-ruststeel" if rusty else "p-chrome"
    tray = "p-rust" if rusty else "p-tray"
    els = []
    for i, (x, z) in enumerate(((2.5, 3.5), (13.5, 3.5), (2.5, 12.5), (13.5, 12.5))):
        if not (rusty and i == 3):
            els += castor(f"Castor{i}", x, z)
        els.append(B(f"Leg{i}", (x - 0.4, 2.25 if not (rusty and i == 3) else 0.5, z - 0.4), (x + 0.4, 12, z + 0.4), frame, faces=no("up", "down")))
    els += [B("Lower", (2, 4, 3), (14, 4.5, 13), tray), B("Top", (1.5, 12, 2.5), (14.5, 12.5, 13.5), tray)]
    els += MK.rim("RimTop", (1.5, 12, 2.5), (14.5, 12.5, 13.5), tray, w=0.4, h=0.75)
    els += MK.rim("RimLow", (2, 4, 3), (14, 4.5, 13), tray, w=0.4, h=0.5)
    els += [B("HandleBar", (14.75, 11, 4), (15.5, 11.75, 12), frame),
            B("HandleA", (14.5, 11, 4), (15.5, 11.75, 4.75), frame), B("HandleB", (14.5, 11, 11.25), (15.5, 11.75, 12), frame)]
    els.append(B("Drape", (2, 12.5, 3), (14, 12.65, 13), "p-drapestain" if rusty else "p-drape", faces=("up",)))
    els += instruments("I", 12.65, rusty, seed=7 if rusty else 3)
    # the lower shelf: gauze packs and a saline bottle
    els += [B("GauzeA", (3, 4.5, 4), (6.5, 5.25, 7), "p-gauze"), B("GauzeB", (3.5, 5.25, 4.5), (6, 5.9, 6.5), "p-gauze")]
    els += rod("Saline", "y", 10, 8, 1.1, 4.5, 8.5, "p-tube")
    els += [B("SalineCap", (9.6, 8.5, 7.6), (10.4, 9.25, 8.4), "p-liqblue")]
    if rusty:
        els += [B("Blood", (8, 4.5, 9), (12, 4.55, 12), "p-blood", faces=("up",))]
    return els


def anaesthesia():
    """An anaesthesia machine: a wheeled grey-green cabinet of drawers, a work shelf, a tower at the back with the
    flowmeter bank and two gauges, a vaporiser at the side, the breathing bag on its hose, the absorber canister,
    and an oxygen and a nitrous oxide cylinder hung at the back."""
    A = "p-anaes"
    els = [B("Base", (1.5, 1.25, 3), (14.5, 2.25, 13), "p-darksteel")]
    for i, (x, z) in enumerate(((2.5, 4), (13.5, 4), (2.5, 12), (13.5, 12))):
        els.append(B(f"Wheel{i}", (x - 0.4, 0, z - 0.6), (x + 0.4, 1.25, z + 0.6), "p-black"))
    els += [B("Body", (2, 2.25, 4), (14, 10, 13), A)]
    for i, (y1, y2) in enumerate(((2.75, 5.25), (5.5, 7.5), (7.75, 9.75))):
        els += [B(f"Drawer{i}", (2.5, y1, 3.6), (13.5, y2, 4), A, faces=no("south")),
                B(f"Pull{i}", (6.5, y2 - 1, 3.1), (9.5, y2 - 0.5, 3.6), "p-chrome", faces=no("south"))]
    els += [B("Shelf", (1.5, 10, 3), (14.5, 11, 13.5), {"top": "p-steel", "side": A}),
            B("Tower", (3, 11, 9.5), (13, 16, 13), A),
            pic(B("Flow", (7, 11.75, 9.25), (12.25, 15.5, 9.5), A, faces=("north",)), "north", "p-flowmeter")]
    els += MK.gauge("GaugeA", 4.75, 14.7, 9.5, r=1.15, angle=-30, face="p-gaugeface", body="p-chrome", needle="p-needle", depth=1.25, stem=False)
    els += MK.gauge("GaugeB", 4.75, 12.2, 9.5, r=1.0, angle=40, face="p-gaugeface", body="p-chrome", needle="p-needle", depth=1.25, stem=False)
    # the vaporiser on the west side, its purple sight glass
    els += [B("Vapo", (0.5, 11, 9.5), (3, 15, 12.5), "p-steel"),
            B("VapoGlass", (0.3, 11.75, 10.25), (0.5, 13.25, 11.75), "p-liqpurple", faces=("west",)),
            B("VapoDial", (0.75, 15, 10), (2.75, 15.75, 12), "p-darkplastic")]
    # the absorber canister on the shelf, a corrugated hose up and over to the bag hanging at the east side
    els += rod("Absorber", "y", 11.5, 6, 1.4, 11, 15, "p-tube")
    els += [B("AbsorberIn", (10.4, 11.5, 4.9), (12.6, 14.25, 7.1), "p-liqpurple", faces=no("up", "down")),
            B("AbsorberLid", (10, 15, 4.5), (13, 15.5, 7.5), "p-darkplastic"),
            B("HoseUp", (13, 12.5, 5.5), (14, 15, 6.5), "p-hose"),
            B("HoseOver", (12.5, 15.05, 5.5), (15, 16, 6.5), "p-hose"),
            B("HoseDown", (14.25, 10.5, 5.5), (15.25, 15, 6.5), "p-hose"),
            B("Bag", (13.75, 5.5, 4.5), (15.75, 10.5, 7.5), "p-breathbag"),
            B("Mask", (12, 11, 3), (14, 12, 5), "p-acrylic")]
    els += rod("CylO2", "y", 5, 14.5, 1.15, 2.5, 10, "p-cylblack")
    els += rod("CylO2Top", "y", 5, 14.5, 1.15, 10.05, 11, "p-cylwhite")
    els += rod("CylN2O", "y", 9, 14.5, 1.15, 2.5, 11, "p-cylblue")
    els += [B("Yoke", (3, 9, 13.25), (11, 9.75, 13.5), "p-darksteel")]
    return els


def equipshelf(part):
    """Steel shelving gone to rust, two blocks high, crowded with old and damaged surgical equipment: a dead machine,
    a toppled case, stacked kidney dishes, jars, an instrument tray, boxes gone soft; moss on a corner."""
    R = "p-ruststeel"
    els = []
    for i, (x, z) in enumerate(((1, 3), (14, 3), (1, 13), (14, 13))):
        els.append(B(f"Post{i}", (x, 0, z), (x + 1, 16, z + 1), R, faces=no("up", "down") if part == "lower" else no("down")))
    shelves = (1, 8.25) if part == "lower" else (6.75, 14.75)
    for i, y in enumerate(shelves):
        els += [B(f"Shelf{i}", (1, y, 3), (15, y + 0.5, 14), R),
                B(f"Lip{i}", (1, y - 0.75, 2.75), (15, y + 0.5, 3), R, faces=no("south"))]
    els += turned([B("BraceA", (1.5, 1, 13.6), (2, 21, 13.9), R, faces=("north", "south"))], rz=-38, origin=(1.75, 1, 13.75)) if part == "lower" else []
    if part == "lower":
        els += [pic(B("Machine", (2.25, 1.5, 4.5), (8.5, 7.25, 12.5), "p-beige-side"), "north", "p-oldmachine"),
                B("MachineKnob", (3, 7.25, 6), (4.5, 7.75, 7.5), "p-black")]
        els += turned([B("BoxA", (9.5, 1.5, 4), (13.5, 5.5, 12.5), "p-cardboard")], ry=7, origin=(11.5, 1.5, 8))
        els += turned([B("BoxB", (10, 5.5, 5), (13, 7.5, 11), "p-cardboard")], ry=-12, origin=(11.5, 5.5, 8))
        for i in range(3):
            els.append(B(f"Dish{i}", (2.5 + i * 0.15, 8.75 + i * 0.5, 4.5), (6.5 + i * 0.15, 9.25 + i * 0.5, 8), "p-tray"))
        els += rod("JarA", "y", 8.5, 6, 1.1, 8.75, 12.5, "p-tube")
        els += [B("JarAIn", (7.6, 8.8, 5.1), (9.4, 11, 6.9), "p-liqamber", faces=("north", "east", "west"))]
        els += rod("JarB", "y", 10.5, 11, 0.9, 8.75, 11.5, "p-tube")
        els += turned([B("Tray", (10, 8.75, 3.5), (14, 9.5, 9), "p-rust"),
                       B("TrayItems", (10.5, 9.5, 4), (13.5, 9.6, 8.5), "p-ruststeel", faces=("up",))], ry=-8, origin=(12, 8.75, 6))
        els += [B("Moss", (2.05, 1.5, 4.05), (5, 2.25, 6), "p-moss"), B("MossHang", (1, 0, 2.5), (3, 1.5, 2.75), "p-vines", faces=("north", "south"))]
    else:
        els += turned([B("Case", (2.5, 0.5, 4), (9, 3, 12), {"all": "p-darkplastic", "top": "p-greyplastic"})], rz=-90, origin=(5.75, 0.5, 8)) \
            if False else turned([B("Case", (2.5, 0.5, 4), (9, 3.5, 12), "p-darkplastic")], ry=14, origin=(5.75, 0.5, 8))
        els += turned([pic(B("Lamp", (10, 0.5, 5), (13.5, 4, 9), "p-lamphead"), "north", "p-lens")], rx=-25, origin=(11.75, 0.5, 7))
        els += [B("Coil", (9.5, 0.55, 10), (13.5, 1.25, 12.9), "p-black")]
        els += turned([B("Toppled", (3, 7.25, 5), (7, 9.25, 12), "p-beige-side")], rz=-60, origin=(7, 7.25, 8.5))
        els += turned([pic(B("OldBox", (8, 7.25, 4.5), (13.5, 11, 12.5), "p-beige-side"), "north", "p-oldmachine")], ry=-5, origin=(10.75, 7.25, 8.5))
        els += [B("TopBox", (3, 15.25, 5), (8, 18, 12), "p-cardboard"),
                B("Moss", (9, 15.25, 4.05), (13.95, 15.75, 8), "p-moss"),
                B("MossHang", (11, 12, 2.6), (14, 15.25, 2.85), "p-vines", faces=("north", "south"))]
    return els


def tuberack():
    """A small steel side table with two wooden racks of test tubes, liquids of every colour in them; moss has grown
    over the racks, and tiny plants grow up out of the tubes."""
    R = "p-ruststeel"
    els = []
    for i, (x, z) in enumerate(((2.5, 3.5), (13.5, 3.5), (2.5, 12.5), (13.5, 12.5))):
        els.append(B(f"Leg{i}", (x - 0.4, 0, z - 0.4), (x + 0.4, 8.5, z + 0.4), R, faces=no("up")))
    els += [B("Top", (2, 8.5, 3), (14, 9.25, 13), {"top": "p-tray", "side": R}),
            B("Shelf", (2.5, 2.5, 3.5), (13.5, 3, 12.5), R)]
    liquids = ["p-liqred", "p-liqgreen", "p-liqamber", "p-liqblue", "p-liqpurple", "p-liqgreen", "p-liqred"]
    rng = random.Random(14)
    for r, z0 in enumerate((4.5, 8.75)):
        els += [B(f"Rack{r}Base", (3, 9.25, z0), (13, 9.75, z0 + 3), "p-rackwood"),
                B(f"Rack{r}TopF", (3, 12, z0 + 0.25), (13, 12.5, z0 + 0.75), "p-rackwood"),
                B(f"Rack{r}TopB", (3, 12, z0 + 2.25), (13, 12.5, z0 + 2.75), "p-rackwood"),
                B(f"Rack{r}EndW", (3, 9.75, z0 + 0.5), (3.5, 12.5, z0 + 2.5), "p-rackwood"),
                B(f"Rack{r}EndE", (12.5, 9.75, z0 + 0.5), (13, 12.5, z0 + 2.5), "p-rackwood")]
        for i in range(6):
            x = 4.4 + i * 1.5
            z = z0 + 1.5
            h = 14.5 - (1.5 if (r, i) in ((0, 4), (1, 1)) else 0)
            liq = liquids[(i + r * 3) % len(liquids)]
            top = 9.75 + rng.uniform(2.5, 4.0)
            els += [B(f"T{r}{i}Liquid", (x - 0.35, 9.75, z - 0.35), (x + 0.35, top, z + 0.35), liq, faces=no("down")),
                    transparent(B(f"T{r}{i}Glass", (x - 0.5, 9.7, z - 0.5), (x + 0.5, h, z + 0.5), "p-tubeglass", faces=no("up", "down")))]
            if (r, i) in ((0, 1), (0, 4), (1, 2), (1, 5)):
                els.append(B(f"T{r}{i}Moss", (x - 0.7, h - 0.2, z - 0.7), (x + 0.7, h + 0.8, z + 0.7), "p-moss"))
            if (r, i) in ((0, 1), (1, 2), (1, 5)):
                s = 2.2
                els += [B(f"T{r}{i}SproutA", (x - s, h + 0.3, z - 0.01), (x + s, h + 4.5, z + 0.01), "p-sprout", faces=("north", "south"), rot=(0, 30 + 40 * i, 0), origin=(x, h, z)),
                        B(f"T{r}{i}SproutB", (x - 0.01, h + 0.3, z - s), (x + 0.01, h + 4.5, z + s), "p-sprout", faces=("east", "west"), rot=(0, 30 + 40 * i, 0), origin=(x, h, z))]
    els += [B("MossTop", (2, 9.25, 3), (6, 9.75, 4.5), "p-moss"), B("MossRack", (8.5, 12.5, 4.5), (13.25, 13.1, 5.5), "p-moss"),
            B("MossLeg", (12.9, 0, 12), (14.1, 2.8, 13.1), "p-moss"),
            B("Drip", (2, 7.5, 2.95), (6, 8.5, 3.05), "p-vines", faces=("north", "south"))]
    return els


def vines():
    """Vegetation spilling over the floor: a mat of leaves with ragged gaps, trailing runners and low sprays of leaves
    standing up from it."""
    els = [B("Mat", (0, 0.05, 0), (16, 0.15, 16), "p-vinemat", faces=("up",))]
    for k, (x, z, a, w, h) in enumerate(((5, 5, 20, 8, 7), (11, 9, -35, 9, 8), (6, 12, 70, 7, 5.5), (12, 3.5, 110, 6, 4.5), (2.5, 13, 5, 5, 4))):
        els.append(B(f"SprayA{k}", (x - w / 2, 0, z - 0.01), (x + w / 2, h, z + 0.01), "p-vines", faces=("north", "south"), rot=(0, a, 0), origin=(x, 0, z)))
        els.append(B(f"SprayB{k}", (x - w / 2, 0, z - 0.01), (x + w / 2, h, z + 0.01), "p-vines", faces=("north", "south"), rot=(0, a + 90, 0), origin=(x, 0, z)))
    for k, (x, z, a) in enumerate(((3, 9, 15), (10, 13, -20), (13, 6, 60))):
        els.append(B(f"Runner{k}", (x - 4, 0.15, z - 1.5), (x + 4, 0.35, z + 1.5), "p-vines", faces=("up",), rot=(0, a, 0), origin=(x, 0.15, z)))
    return els


def mouldfloor():
    """A black-green mould carpet, a thin layer with ragged holes where the floor shows, and fuzzy clumps on it."""
    els = [B("Layer", (0, 0.02, 0), (16, 0.3, 16), "p-mouldfloor", faces=("up",))]
    for k, (x, z, s, h) in enumerate(((3, 4, 2.5, 0.9), (10, 6, 3, 1.2), (6, 11, 2, 0.7), (13, 13, 2.5, 1.0), (12, 2, 1.5, 0.6))):
        els.append(B(f"Clump{k}", (x - s / 2, 0.2, z - s / 2), (x + s / 2, 0.2 + h, z + s / 2), "p-mould", faces=no("down")))
    return els


# ======================================================================== Torture chambers

def stretcher(name, y, x=8, z=8, ry=0, rz=0):
    """A rusted canvas stretcher lying along z, centred on (x, z), its feet on y: two poles, the stained canvas between
    them, spreader bars and four short feet."""
    els = [B(name + "PoleW", (x - 4.5, y + 1, z - 7.75), (x - 3.75, y + 1.75, z + 7.75), "p-rust"),
           B(name + "PoleE", (x + 3.75, y + 1, z - 7.75), (x + 4.5, y + 1.75, z + 7.75), "p-rust"),
           B(name + "Canvas", (x - 3.75, y + 1.15, z - 5.6), (x + 3.75, y + 1.5, z + 5.6), "p-canvas"),
           B(name + "BarN", (x - 3.75, y + 0.9, z - 5.75), (x + 3.75, y + 1.3, z - 5.25), "p-rust"),
           B(name + "BarS", (x - 3.75, y + 0.9, z + 5.25), (x + 3.75, y + 1.3, z + 5.75), "p-rust")]
    for i, (fx, fz) in enumerate(((x - 4.1, z - 4.5), (x + 4.1, z - 4.5), (x - 4.1, z + 4.5), (x + 4.1, z + 4.5))):
        els.append(B(f"{name}Foot{i}", (fx - 0.35, y, fz - 0.35), (fx + 0.35, y + 1, fz + 0.35), "p-rust", faces=no("up")))
    return turned(els, ry=ry, rz=rz, origin=(x, y, z))


def stretchers(part):
    """Rusted stretchers stacked atop each other, askew, a block and a half high (lower, upper)."""
    els = []
    if part == "lower":
        for i, (y, x, z, ry, rz) in enumerate(((0, 8, 8, 0, 0), (2.4, 7.3, 8.6, 9, 2), (4.9, 8.7, 7.4, -7, -3),
                                                 (7.4, 7.6, 8.3, 14, 1), (9.9, 8.8, 8.5, -4, 4), (12.4, 7.4, 7.6, 10, -2))):
            els += stretcher(f"S{i}", y, x, z, ry, rz)
        els += [B("BloodDrip", (3.4, 3.5, 2.5), (3.6, 9, 3.5), "p-blood", faces=("west", "north", "east"))]
    else:
        for i, (y, x, z, ry, rz) in enumerate(((-1.1, 8.3, 8.2, -9, 1), (1.4, 7.6, 7.8, 4, -3), (3.9, 8.6, 8.6, -14, 2))):
            els += stretcher(f"S{i}", y, x, z, ry, rz)
        els += stretcher("Slid", 6.6, 9, 7, 28, -10)
    return els


def knifecab(part):
    """A rusted metal cabinet, two blocks high, its glazed doors (one pane cracked) showing rows of shining knives,
    scalpels and razor blades: painted on its back, real ones hanging from magnetic bars in front."""
    return glass_cabinet(part, "p-rustcab", glass_tex=("p-glasscrack", "p-glass") if part == "upper" else ("p-glass", "p-glasscrack"),
                         back="p-knives", knives=True)


def chain(name, x, z, top, n, tex="p-rust"):
    """A hanging chain of n links from `top` down: oval links of four bars, each turned a quarter from the last."""
    els = []
    L, W, t = 1.9, 1.15, 0.3
    hw = W / 2
    for i in range(n):
        y2 = top - i * (L - 0.55)
        y1 = y2 - L
        if i % 2 == 0:
            els += [B(f"{name}{i}a", (x - hw, y1 + t, z - t / 2), (x - hw + t, y2 - t, z + t / 2), tex),
                    B(f"{name}{i}b", (x + hw - t, y1 + t, z - t / 2), (x + hw, y2 - t, z + t / 2), tex),
                    B(f"{name}{i}c", (x - hw + 0.1, y2 - t, z - t / 2), (x + hw - 0.1, y2, z + t / 2), tex),
                    B(f"{name}{i}d", (x - hw + 0.1, y1, z - t / 2), (x + hw - 0.1, y1 + t, z + t / 2), tex)]
        else:
            els += [B(f"{name}{i}a", (x - t / 2, y1 + t, z - hw), (x + t / 2, y2 - t, z - hw + t), tex),
                    B(f"{name}{i}b", (x - t / 2, y1 + t, z + hw - t), (x + t / 2, y2 - t, z + hw), tex),
                    B(f"{name}{i}c", (x - t / 2, y2 - t, z - hw + 0.1), (x + t / 2, y2, z + hw - 0.1), tex),
                    B(f"{name}{i}d", (x - t / 2, y1, z - hw + 0.1), (x + t / 2, y1 + t, z + hw - 0.1), tex)]
    return els


def hook():
    """Rusted chains hanging in the top block of a room from an anchor plate, a meat hook on the longest, an open
    shackle on the other."""
    els = [B("Anchor", (6.5, 15.5, 6.5), (10.5, 16, 9.5), "p-rust"),
           B("AnchorB", (10.5, 15.5, 10), (13, 16, 12), "p-rust")]
    els += chain("Chain", 8.5, 8, 15.5, 8)
    els += chain("ChainB", 11.75, 11, 15.5, 5)
    # the meat hook: a shank, the curve and the point, bloodied
    els += [B("Ring", (8.0, 3.6, 7.75), (9.0, 4.4, 8.25), "p-hook"),
            B("Shank", (8.25, 1.25, 7.75), (8.75, 3.6, 8.25), "p-hook"),
            B("Curve", (8.25, 0.75, 7.75), (11.25, 1.25, 8.25), "p-hook"),
            B("Rise", (10.75, 1.25, 7.75), (11.25, 3.0, 8.25), "p-hook")]
    els += turned([B("Point", (10.8, 3.0, 7.8), (11.2, 4.25, 8.2), "p-hook")], rz=20, origin=(11, 3.0, 8))
    els += [B("ShackleA", (11.0, 7.4, 10.8), (11.35, 9.0, 11.2), "p-rust"), B("ShackleB", (12.15, 7.4, 10.8), (12.5, 9.0, 11.2), "p-rust"),
            B("ShackleC", (11.0, 7.0, 10.8), (12.5, 7.4, 11.2), "p-rust"),
            B("Drop", (8.35, 0.1, 7.85), (8.65, 0.6, 8.15), "p-blood")]
    return els


def bloodpool():
    """A pool of blood on the floor, glossy, and drops round it."""
    els = [pic(B("Pool", (0.5, 0.02, 0.5), (15.5, 0.08, 15.5), "p-blood", faces=("up",)), "up", "p-bloodpool")]
    for k, (x, z, s) in enumerate(((2, 13.5, 0.75), (13.5, 14, 0.5), (14.5, 2.5, 0.6), (1.5, 2, 0.4))):
        els.append(B(f"Drop{k}", (x - s, 0.02, z - s), (x + s, 0.1, z + s), "p-blood", faces=("up",)))
    return els


# ======================================================================== T.14.R.G.

def field_table():
    """The research group's field table: an olive steel top on tubular legs with a cross brace."""
    O = "p-olive"
    els = [B("Top", (0.5, 11.5, 2), (15.5, 12.5, 14), {"top": O, "side": O}),
           B("Apron", (1, 10.25, 2.25), (15, 11.5, 2.75), O, faces=no("up", "south"))]
    for i, (x, z) in enumerate(((1.75, 3.25), (14.25, 3.25), (1.75, 12.75), (14.25, 12.75))):
        els.append(B(f"Leg{i}", (x - 0.45, 0, z - 0.45), (x + 0.45, 11.5, z + 0.45), "p-darksteel", faces=no("up")))
    els += [B("BraceW", (1.4, 3, 3.7), (2.1, 3.6, 12.3), "p-darksteel"), B("BraceE", (13.9, 3, 3.7), (14.6, 3.6, 12.3), "p-darksteel"),
            B("BraceX", (2.1, 3, 7.7), (13.9, 3.6, 8.3), "p-darksteel")]
    return els


def trgdesk(kind):
    els = field_table()
    y = 12.5
    if kind == "papers":
        for i, (x, z, a) in enumerate(((4, 6, 6), (4.6, 6.3, -4), (11, 8, 18), (8, 10.5, -25))):
            els += turned([pic(B(f"Sheet{i}", (x - 2.25, y + i * 0.1, z - 3), (x + 2.25, y + i * 0.1 + 0.1, z + 3), "p-papers", faces=("up",)),
                               "up", "p-trgpaper" if i % 2 == 0 else "p-papers")], ry=a, origin=(x, y, z))
        els += [B("Stack", (1.5, y, 9), (6, y + 2, 13), {"top": "p-folder", "side": "p-linenstack"}),
                B("Box", (11, y, 2.5), (15, y + 3, 6), "p-cardboard"),
                B("BoxFiles", (11.5, y + 3, 3), (14.5, y + 4, 5.5), "p-folder", faces=("up", "north", "east", "west")),
                B("Pen", (7, y + 0.4, 4), (7.3, y + 0.7, 7.5), "p-liqblue")]
        els += rod("Mug", "y", 13.25, 11.5, 0.95, y, y + 2, {"side": "p-olive", "top": "p-black"})
    elif kind == "radio":
        els += [B("Radio", (2.5, y, 5), (10, y + 5.5, 11), {"all": "p-olive", "top": "p-darksteel"}),
                pic(B("Face", (3, y + 0.5, 4.75), (9.5, y + 5, 5), "p-olive", faces=("north",)), "north", "p-radioface"),
                B("Handle", (4, y + 5.5, 7.5), (8.5, y + 6.25, 8.5), "p-black"),
                B("Antenna", (9.2, y + 5.5, 10.2), (9.5, 30, 10.5), "p-chrome", rot=(0, 0, -6), origin=(9.35, y + 5.5, 10.35)),
                B("Handset", (11, y, 4.5), (12.5, y + 1.25, 9.5), "p-black"),
                B("Cord", (10, y, 7), (11, y + 0.5, 7.5), "p-black"),
                pic(B("Pad", (11.5, y, 10), (15, y + 0.3, 13.5), "p-papers", faces=no("down")), "up", "p-papers"),
                B("PhonesBand", (12.5, y, 2.5), (14.5, y + 2, 3), "p-black"),
                B("PhonesA", (12, y, 1.9), (13, y + 1, 3.6), "p-black"), B("PhonesB", (14, y, 1.9), (15, y + 1, 3.6), "p-black")]
    else:
        # an open sample case, foam-lined, its vials; a microscope beside it
        els += [B("Case", (2, y, 4), (9.5, y + 1.5, 11), "p-steel"),
                B("Foam", (2.5, y + 1.5, 4.5), (9, y + 1.6, 10.5), "p-black", faces=("up",)),
                B("Lid", (2, y + 1.5, 11), (9.5, y + 8.5, 11.75), {"all": "p-steel", "front": "p-black"})]
        for i in range(8):
            x, z = 3.25 + (i % 4) * 1.75, 6 + (i // 4) * 2.75
            if i == 5:
                continue
            els += [B(f"Vial{i}", (x - 0.4, y + 1.5, z - 0.4), (x + 0.4, y + 3.5, z + 0.4), "p-vial", glow=60),
                    B(f"VialCap{i}", (x - 0.45, y + 3.5, z - 0.45), (x + 0.45, y + 4, z + 0.45), "p-vialglow", glow=110)]
        els += turned([B("VialOut", (10, y, 3), (10.8, y + 0.8, 5), "p-vial", glow=60)], ry=35, origin=(10.4, y, 4))
        els += [B("ScopeBase", (11, y, 7), (14.5, y + 0.75, 11.5), "p-darkplastic"),
                B("ScopeArm", (12.5, y + 0.75, 10), (13.75, y + 6, 11.25), "p-darkplastic"),
                B("ScopeStage", (11, y + 2.5, 7.5), (14.5, y + 3, 10), "p-darksteel")]
        els += turned([B("ScopeTube", (12.4, y + 3.5, 7.9), (13.4, y + 8, 8.9), "p-steel")], rx=-15, origin=(12.9, y + 6, 9.5))
    return els


def samplerack():
    """A steel rack of Compound 14: rows of black vials in holders on three shelves, a dull sickly green glow in them,
    the placard on its top rail."""
    S = "p-darksteel"
    els = []
    for i, (x, z) in enumerate(((1.25, 4.5), (14, 4.5), (1.25, 11), (14, 11))):
        els.append(B(f"Post{i}", (x, 0, z), (x + 0.75, 15, z + 0.75), S, faces=no("down")))
    for k, y in enumerate((1.25, 6, 10.75)):
        els += [B(f"Shelf{k}", (1.25, y - 0.5, 4.5), (14.75, y, 11.75), S),
                B(f"Holder{k}", (2, y + 0.5, 6.5), (14, y + 1.25, 9.5), "p-steel")]
        for i in range(8):
            x = 2.75 + i * 1.5
            for r, z in enumerate((7.25, 8.75)):
                if (k, i, r) in ((1, 3, 0), (2, 6, 1), (0, 5, 0)):
                    continue
                els += [B(f"V{k}{i}{r}", (x - 0.45, y, z - 0.45), (x + 0.45, y + 3.25, z + 0.45), "p-vial", glow=45),
                        B(f"C{k}{i}{r}", (x - 0.5, y + 3.25, z - 0.5), (x + 0.5, y + 3.75, z + 0.5), "p-vialglow", glow=100)]
    els += [B("Rail", (1.25, 14.25, 4.25), (14.75, 15.25, 4.5), S, faces=no("south")),
            pic(B("Placard", (4, 13, 4), (12, 15.75, 4.25), S, faces=("north", "up", "down", "east", "west")), "north", "p-c14label", glow=0)]
    els[-1]["faces"]["north"]["uv"] = [0, 0, 16, 16]
    els += [B("Spill", (3, 1.25, 5), (7, 1.3, 7.5), "p-oozeflat", faces=("up",), glow=90)]
    return els


def cell(part, state):
    """A containment chamber's thick glass panel in a bolted steel frame, along the block's north edge. broken: smashed
    out from inside (from beyond the glass): jagged pieces left in the frame, shards strewn over this block's floor."""
    F = "p-darksteel"
    lower = part == "lower"
    els = [B("PostW", (0, 0, 0), (1.75, 16, 2.5), F, faces=no("up", "down")),
           B("PostE", (14.25, 0, 0), (16, 16, 2.5), F, faces=no("up", "down"))]
    if lower:
        els += [B("Sill", (1.75, 0, 0), (14.25, 2, 2.5), F, faces=no("down", "east", "west")),
                B("Hazard", (1.75, 0.5, -0.05), (14.25, 1.5, 0), "p-drum", faces=("north",))]
        gy1, gy2 = 2, 16
    else:
        els += [B("HeadRail", (1.75, 14, 0), (14.25, 16, 2.5), F, faces=no("up", "east", "west"))]
        gy1, gy2 = 0, 14
    for i, (x, y) in enumerate(((0.85, 3), (0.85, 9), (0.85, 14), (15.15, 3), (15.15, 9), (15.15, 14))):
        els.append(B(f"Bolt{i}", (x - 0.4, y - 0.4, -0.25), (x + 0.4, y + 0.4, 0), "p-chrome", faces=no("south")))
    els += [B("GasketW", (1.75, gy1, 0.6), (2.1, gy2, 1.9), "p-black", faces=("east",)),
            B("GasketE", (13.9, gy1, 0.6), (14.25, gy2, 1.9), "p-black", faces=("west",))]
    if state == "intact":
        els.append(transparent(B("Glass", (1.75, gy1, 0.75), (14.25, gy2, 1.75), "p-cellglass", faces=("north", "south"))))
        return els
    # jagged pieces still in the frame
    if lower:
        pieces = [((2.1, 2, 0.8), (5.5, 7, 1.7), 0, 0, 18), ((10.5, 2, 0.8), (13.9, 5, 1.7), 0, 0, -12),
                  ((2.1, 7, 0.8), (3.5, 14, 1.7), 0, 0, 6), ((12.75, 4.5, 0.8), (13.9, 12, 1.7), 0, 0, -7)]
    else:
        pieces = [((2.1, 7, 0.8), (6.5, 14, 1.7), 0, 0, -16), ((9, 9.5, 0.8), (13.9, 14, 1.7), 0, 0, 14),
                  ((2.1, 0, 0.8), (3.4, 7, 1.7), 0, 0, -5), ((12.5, 1, 0.8), (13.9, 9.5, 1.7), 0, 0, 9)]
    for i, (frm, to, rx, ry, rz) in enumerate(pieces):
        el = transparent(B(f"Jag{i}", frm, to, "p-cellglass", faces=("north", "south", "up")))
        els += turned([el], rz=rz, origin=((frm[0] + to[0]) / 2, frm[1] if lower else to[1], 1.25))
    if lower:
        rng = random.Random(1404)
        for i in range(11):
            x, z = rng.uniform(2.5, 13.5), rng.uniform(3, 13.5)
            w, d = rng.uniform(0.8, 2.6), rng.uniform(0.6, 1.8)
            els.append(B(f"Shard{i}", (x - w / 2, 0, z - d / 2), (x + w / 2, rng.uniform(0.15, 0.35), z + d / 2), "p-shard",
                         faces=no("down"), rot=(0, rng.uniform(-80, 80), 0), origin=(x, 0, z)))
        els += [B("Ooze", (5, 2, 0.4), (10, 2.05, 2.2), "p-oozeflat", faces=("up",), glow=80),
                B("OozeRun", (6, 0.5, 2.5), (7, 2, 2.55), "p-oozeflat", faces=("south",), glow=80)]
    return els


def crate():
    """A T.14.R.G. supply crate: planked, battened, stencilled on its front, rope handles at its ends."""
    C, D = "p-crate", "p-veneer-side"
    els = [B("Box", (1.5, 0, 2), (14.5, 12.5, 14), {"all": C, "front": C}),
           pic(B("Front", (1.5, 0.75, 1.75), (14.5, 11.75, 2), C, faces=("north",)), "north", "p-cratestencil"),
           B("Lid", (1, 12.5, 1.5), (15, 13.5, 14.5), C)]
    for i, (x1, x2) in enumerate(((1.25, 2.75), (13.25, 14.75))):
        els += [B(f"CornerN{i}", (x1, 0, 1.25), (x2, 12.5, 2.25), D), B(f"CornerS{i}", (x1, 0, 13.75), (x2, 12.5, 14.75), D)]
    for i, y in enumerate((0, 10.75)):
        els += [B(f"BattenN{i}", (2.75, y, 1.4), (13.25, y + 1.5, 2), D, faces=no("south")),
                B(f"BattenS{i}", (2.75, y, 14), (13.25, y + 1.5, 14.6), D, faces=no("north"))]
    for i, x in enumerate((1.5, 14.5)):
        d = -1 if i == 0 else 1
        x0 = x if d > 0 else x - 0.6
        els += [B(f"Rope{i}", (x0, 7, 6), (x0 + 0.6, 7.6, 10), "p-canvas"),
                B(f"RopeA{i}", (x0, 7, 6), (x0 + 0.6, 9, 6.6), "p-canvas"), B(f"RopeB{i}", (x0, 7, 9.4), (x0 + 0.6, 9, 10), "p-canvas")]
    return els


def drum(state):
    """A steel drum, the radiation trefoil on it. leaking: rusted through, green ooze running down it and pooling,
    glowing, on the floor round it."""
    leak = state == "leaking"
    side = "p-drumrust" if leak else "p-drum"
    sign = "p-drumsignrust" if leak else "p-drumsign"
    els = octagon("Drum", 8, 8, 6, 0, 14, {"side": side, "top": "p-drum", "bottom": "p-drum"})
    els += octagon("HoopA", 8, 8, 6.25, 4.25, 5, side, faces=("north", "south", "east", "west", "up", "down"))
    els += octagon("HoopB", 8, 8, 6.25, 9.25, 10, side, faces=("north", "south", "east", "west", "up", "down"))
    els += octagon("Chime", 8, 8, 6.2, 13.25, 14.25, side)
    els += [pic(B("Lid", (3.5, 14.25, 3.5), (12.5, 14.3, 12.5), "p-drumtop", faces=("up",)), "up", "p-drumtop"),
            B("Bung", (5, 14.25, 5.5), (6.5, 14.75, 7), "p-darksteel"),
            pic(B("SignN", (5.1, 5.25, 1.9), (10.9, 9, 2.0), side, faces=("north",)), "north", sign, uv=(2, 3, 14, 13)),
            pic(B("SignS", (5.1, 5.25, 14.0), (10.9, 9, 14.1), side, faces=("south",)), "south", sign, uv=(2, 3, 14, 13))]
    if leak:
        els += [pic(B("Pool", (0, 0.02, 0), (16, 0.08, 16), "p-oozeflat", faces=("up",)), "up", "p-ooze", glow=170),
                B("Run", (6.5, 0.5, 1.85), (8, 9.5, 1.95), "p-oozeflat", faces=("north",), glow=150),
                B("RunB", (13.95, 0.5, 9), (14.05, 6, 10.25), "p-oozeflat", faces=("east",), glow=150),
                B("Hole", (6.75, 8.5, 1.8), (7.75, 9.5, 1.9), "p-black", faces=("north",))]
    return els


# ======================================================================== Halls

DIRS_ALL = ("north", "east", "south", "west", "up", "down")
COUNTER = {"front": "p-laminate", "back": "p-whiteworn", "side": "p-whiteworn", "top": "p-whiteworn", "bottom": "p-whiteworn"}
SLEDGE = {"top": "p-mintlam", "side": "p-teal", "bottom": "p-whiteworn"}


def station_run(x0=0.0, ends=()):
    """The straight counter of a nurses' station: a white laminate front over a teal kick, a mint transaction ledge,
    the work surface behind, a file pedestal under it. x0 starts the run's front parts further east (at a corner),
    `ends` keeps their faces at those ends ("west")."""
    f = no("down") if "west" in ends else no("east", "west", "down")
    f2 = DIRS_ALL if "west" in ends else no("east", "west")
    els = [B("Kick", (max(x0, 1.5) if x0 else 0, 0, 1.5), (16, 1.5, 3), "p-teal", faces=("north", "up") + (("west",) if "west" in ends else ())),
           B("Front", (max(x0, 1) if x0 else 0, 1.5, 1), (16, 16, 3), COUNTER, faces=f),
           B("Band", (max(x0, 0.75) if x0 else 0, 12.5, 0.75), (16, 13.25, 1), "p-teal", faces=("north", "up", "down") + (("west",) if "west" in ends else ())),
           B("Ledge", (max(x0, 0.25) if x0 else 0, 16, 0.25), (16, 17, 5.5), SLEDGE, faces=f2),
           B("Work", (max(x0, 3) if x0 else 0, 11, 3), (16, 12, 13), WORK, faces=f2)]
    if not x0:
        els.append(B("Pedestal", (1, 0, 4), (6, 11, 12.5), "p-whiteworn", faces=("south", "east", "west")))
        for i, (y1, y2) in enumerate(((0.75, 5.5), (5.75, 10.5))):
            els += [B(f"File{i}", (1.25, y1, 12.5), (5.75, y2, 12.9), "p-white", faces=no("north")),
                    B(f"FilePull{i}", (2.5, y2 - 1.25, 12.9), (4.5, y2 - 0.75, 13.4), "p-chrome", faces=no("north"))]
    return els


def station(part):
    if part == "corner":
        # an L: the run along the north edge (from the corner east) meets one along the west edge (its front to the
        # west, from the corner south); the north arm owns the corner itself
        els = station_run(x0=0.25, ends=("west",))
        west = turn(station_run(), 3)    # front north -> front west
        start = {"Kick": 3, "Front": 3, "Band": 1, "Ledge": 5.5, "Work": 13}
        for e in west:
            if e["name"] not in start:
                continue
            e["from"] = [e["from"][0], e["from"][1], start[e["name"]]]
            e["name"] = "W" + e["name"]
            els.append(e)
        els.append(B("CornerPost", (0.5, 0, 0.5), (1.5, 17.5, 1.5), "p-teal"))
        return els
    els = station_run()
    y = 12
    if part == "computer":
        # a beige CRT monitor and keyboard facing the nurse (south), the tower beside it
        els += [B("Crt", (3.5, y + 0.5, 6.5), (11.5, y + 6.5, 11), {"all": "p-beige", "side": "p-beige-side", "back": "p-beige-side"}),
                B("CrtBack", (4.75, y + 1.25, 5.75), (10.25, y + 5.75, 6.5), "p-beige-side"),
                B("CrtFoot", (5.5, y, 7.5), (9.5, y + 0.5, 10.5), "p-beige-side"),
                pic(B("Screen", (4.25, y + 1.25, 11), (10.75, y + 5.75, 11.15), "p-black", faces=("south",)), "south", "p-crt", glow=60),
                pic(B("Keyboard", (4, y, 11.4), (11, y + 0.6, 12.9), "p-beige-side", faces=no("down")), "up", "p-keyboard"),
                B("Tower", (12, y, 6), (14.75, y + 4.75, 12.4), {"all": "p-beige", "side": "p-beige-side"}),
                B("Drive", (12.4, y + 3.5, 12.4), (14.35, y + 4, 12.5), "p-darkplastic", faces=("south",)),
                B("Mouse", (11.25, y, 12.1), (11.95, y + 0.5, 12.85), "p-beige")]
    else:
        els += [B("Binder", (3, y, 6), (5, y + 3.75, 12), {"all": "p-liqblue", "top": "p-papers"}),
                B("BinderB", (5.1, y, 6.5), (6.9, y + 3.5, 12), {"all": "p-liqred", "top": "p-papers"})]
        els += turned([pic(B("Sheet", (8, y, 6), (12.5, y + 0.1, 12), "p-papers", faces=("up",)), "up", "p-chart")], ry=10, origin=(10, y, 9))
        els += [pic(B("Sign", (5, 17, 1), (11, 17.15, 4.5), "p-papers", faces=("up",)), "up", "p-papers")]
    return els


def linencart():
    """A linen cart: a chrome frame on castors, three shelves of folded sheets and blankets, a blue laundry sack on
    the bottom shelf, a stained sheet thrown on top."""
    els = []
    for i, (x, z) in enumerate(((2, 3.5), (14, 3.5), (2, 12.5), (14, 12.5))):
        els += castor(f"Castor{i}", x, z)
        els.append(B(f"Post{i}", (x - 0.4, 2.25, z - 0.4), (x + 0.4, 15.25, z + 0.4), "p-chrome", faces=no("down")))
    for k, y in enumerate((2.5, 8, 14.5)):
        els.append(B(f"Shelf{k}", (1.5, y, 3), (14.5, y + 0.5, 13), "p-steel"))
    linen = {"top": "p-sheet", "side": "p-linenstack", "front": "p-linenstack"}
    els += [B("Sack", (2.5, 3, 4), (8, 7.5, 12), "p-linenbag"), B("SackTie", (4.5, 7.5, 7.5), (6, 8, 8.5), "p-linenbag"),
            B("StackA", (8.75, 3, 4), (13.5, 6.5, 12), linen),
            B("StackB", (2.5, 8.5, 4), (7.5, 12.5, 12), linen),
            B("StackC", (8.5, 8.5, 4.5), (13.5, 11.5, 11.5), {"top": "p-blanket", "side": "p-blanket-side"}),
            B("StackD", (3, 15, 4.5), (8, 16.5, 11.5), linen)]
    els += turned([B("Thrown", (7, 15, 3.5), (14, 16, 12), "p-sheetstain")], ry=12, origin=(10.5, 15, 7.75))
    els += turned([B("ThrownHang", (13.5, 10.5, 4), (14, 16, 10), "p-sheetstain")], rz=-8, origin=(14, 16, 7))
    return els


def bench():
    """A hall bench facing north: pale wooden slats on a dark steel frame, a back leaning a little back."""
    D = "p-darksteel"
    els = []
    for i, x in enumerate((1.25, 14)):
        els += [B(f"LegF{i}", (x, 0, 3), (x + 0.75, 7, 3.75), D), B(f"LegB{i}", (x, 0, 11), (x + 0.75, 7, 11.75), D),
                B(f"Rail{i}", (x, 6.25, 3), (x + 0.75, 7, 11.75), D),
                B(f"Arm{i}", (x - 0.25, 10, 3.5), (x + 1, 10.75, 12), "p-benchwood"),
                B(f"ArmPost{i}", (x, 7, 4), (x + 0.75, 10, 4.75), D),
                B(f"Upright{i}", (x, 7, 11), (x + 0.75, 15, 11.75), D, rot=(8, 0, 0), origin=(x, 7, 11.75))]
    for k, (z1, z2) in enumerate(((3, 5.5), (5.9, 8.4), (8.8, 11.3))):
        els.append(B(f"Seat{k}", (0.75, 7, z1), (15.25, 7.75, z2), "p-benchwood"))
    els += turned([B("BackA", (0.75, 9, 11.75), (15.25, 11.25, 12.5), "p-benchwood"),
                   B("BackB", (0.75, 12, 11.75), (15.25, 14.25, 12.5), "p-benchwood")], rx=8, origin=(8, 7, 11.75))
    els += [B("Brace", (2, 1.5, 11), (14, 2.25, 11.75), D)]
    return els
