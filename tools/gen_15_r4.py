"""Level 15, "Futuristic Halls" (experimental), round 4's blocks (the asset-quality pass, 2026-11-02): round 3's props
rebuilt as real objects (several boxes an element, rotated parts, lit screens), and the new set pieces. Run after
gen_15.py, gen_15_links.py and gen_15_r3.py (it reads their textures and rewrites some of round 3's shapes in place,
so the block codes do not change):
    python tools/gen_15_r4.py      (under tools/locked.sh run)

Rewritten shapes (same files, same blocks):
    l15-console     a console desk: plinth, cheeks, a sloped keyboard and trackball, a monitor on a neck, tilted back
    l15-dock        the charging dock: chamfered cheeks, contact arms, a charging pad with guide rails and studs, a hood
                    with a lit edge, a charge display; the Robo-Man's eyes lit while the dock has power
    l15-seat        lecture seats: side standards with arm pads, a cushion with a front roll, a back in two pitches on a
                    shell, a tablet folded down on its pivot, a seat number
    l15-riser       the half step gets an aisle light in its nosing
    l15-serve       the serving line: a tubular tray slide, wells with pans and a ladle, a heat-lamp gantry and an angled
                    sneeze guard in a steel frame, the till with its screen and a cash drawer
    l15-growrack    hydroponics racks: channels with net pots and small dead plants, a feed line with drippers, a return
                    pipe, LED bars in housings, posts with feet
    l15-curtain     the bay curtain on a ceiling track with gliders, a mesh band, pleats (rotated), rods to the ceiling
    l15-hangsign    the hall signs in a steel frame, their lower edge lit, ceiling plates on the rods
New blocks:
    l15-panel       a white wall block with a model on its face (toward its side): the fire extinguisher (the detail kit's
                    own, on 15's panel), the ESCAPE panel in a bezel with a real mushroom button, the lift (leaves recessed
                    in a proud steel portal, the indicator as a lit display, the call panel with buttons), the big display's
                    bezel, the bulkheads' jambs, the battery emergency lamp and the tripped breaker panel by the dark
    l15-bulkhead    the deep header of a bulkhead across a main hall (lit, dead; we, ns)
    l15-glazing     the thick glass walls in a steel frame: sill, head, a mullion every block (clear, cracked)
    l15-medmonitor  a vitals monitor on a wall arm over a medical bed's head, on a headwall rail (lit, dead)
    l15-stool       a canteen's fixed stool; l15-ctable: a canteen table (laminate on a pedestal)
Lettering as gen_15_r3. All text is the facility's, invented.
"""
import json
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw

import matlib as M
from modelkit import box
from gen_15 import (BLOCKS, CLOTH, GLASS, METAL, ROOT, ROTATE, S, SHAPES, SIDES, STONE, TEX, WOOD, blend, cuboid, json_block,
                    rect, save, write_json)
from gen_15_r3 import B, LINE_COLOURS, draw_text, write_shape, T

ASSETS = os.path.join(ROOT, "assets", "backrooms")


def opaque(img):
    """No translucent texels in the opaque pass: alpha to 0 or 255."""
    a = np.array(img.convert("RGBA"))
    a[..., 3] = np.where(a[..., 3] >= 128, 255, 0)
    return Image.fromarray(a, "RGBA")


def load(name):
    return Image.open(os.path.join(TEX, name + ".png")).convert("RGBA")


# ======================================================================== Textures

def textures():
    # Bright brushed stainless (frames, portals, rails), its painted white twin, a dark matte plastic (bezels, housings)
    save(M.brushed_metal(seed=15800, base=(196, 200, 204), direction="h", streak=4, sheen=9), "brushed")
    save(M.brushed_metal(seed=15801, base=(196, 200, 204), direction="v", streak=4, sheen=9), "brushedv")
    bez = M.rubber(seed=15802, base=(44, 46, 50))
    save(bez, "bezel")
    save(M.painted_metal(seed=15803, base=(232, 234, 234), panel=False, chips=0), "whitegloss")
    # Keyboard: keycaps in rows on a dark tray, a lighter space bar
    img = M.new((S, S), (30, 32, 36))
    for row, y in enumerate(range(1, 15, 3)):
        x = 1 + (row % 2)
        while x < 30:
            w = 2 if not (row == 4 and 9 <= x <= 20) else 10
            rect(img, x, y, min(30, x + w - 1), y + 1, (92, 96, 102))
            rect(img, x, y, min(30, x + w - 1), y, (132, 136, 142))
            x += w + 1
    save(img, "keys")
    # The sneeze guard's glass as a cut-out (alpha 0 or 255): its edges and a few diagonal glints, nothing between
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for k in range(S):
        for x, y in ((k, 0), (k, 31), (0, k), (31, k)):
            img.putpixel((x, y), (214, 232, 236, 255))
    for x0 in (4, 9, 22):
        for k in range(10):
            if 0 <= x0 + k < S and 3 + k < S:
                img.putpixel((x0 + k, 3 + k), (236, 248, 252, 255))
    save(img, "guardcut")
    # The consoles' screens at 64 px, the picture in the top 40 rows (the screens are 16:10)
    for name, kind in (("cscreen-dead", 0), ("cscreen-denied", 1), ("cscreen-radar", 2)):
        img = Image.new("RGBA", (B, B), (0, 0, 0, 255))
        if kind == 0:
            rect(img, 0, 0, B - 1, 39, (16, 18, 22))
            for k in range(16):
                blend(img, 10 + k, 4 + k // 2, (64, 70, 80), 0.5)
                blend(img, 12 + k, 4 + k // 2, (54, 60, 70), 0.3)
        elif kind == 1:
            rect(img, 0, 0, B - 1, 39, (36, 6, 6))
            rect(img, 0, 0, B - 1, 6, (120, 20, 16))
            draw_text(img, (2, 0, B - 2, 6), "AVALON 2.4  //  TERMINAL 15", (255, 210, 200), 4, condensed=True)
            draw_text(img, (4, 10, B - 4, 22), "ACCESS DENIED", (255, 96, 84), 8, condensed=True)
            draw_text(img, (4, 24, B - 4, 30), "LEVEL 5 CLEARANCE REQUIRED", (220, 120, 110), 4, condensed=True)
            rect(img, 4, 33, 30, 35, (120, 40, 34))
            draw_text(img, (4, 32, B - 4, 37), ">_", (255, 120, 100), 4, condensed=True)
        else:
            rect(img, 0, 0, B - 1, 39, (4, 16, 8))
            d = ImageDraw.Draw(img)
            for r in (6, 12, 18):
                d.ellipse((32 - r * 1.3, 21 - r, 32 + r * 1.3, 21 + r), outline=(30, 110, 56, 255))
            d.line((32, 21, 54, 9), fill=(150, 255, 170, 255))
            for nx, ny in ((18, 14), (44, 27), (24, 30), (40, 12), (50, 22)):
                d.rectangle((nx - 1, ny - 1, nx + 1, ny + 1), fill=(200, 255, 200, 255))
            d.line((18, 14, 40, 12), fill=(70, 200, 110, 255))
            d.line((40, 12, 50, 22), fill=(70, 200, 110, 255))
            d.line((44, 27, 24, 30), fill=(70, 200, 110, 255))
            draw_text(img, (2, 1, 34, 6), "AVALON 2.4", (110, 250, 140), 4, condensed=True)
        save(img, name)
    # Status LEDs, a contact's copper, a hazard band (yellow and black diagonals), a heat lamp's glowing element
    save(M.new((S, S), (90, 255, 140)), "ledgreen")
    save(M.new((S, S), (255, 170, 60)), "ledamber")
    save(M.new((S, S), (255, 70, 50)), "ledred")
    save(M.brushed_metal(seed=15804, base=(184, 120, 70), direction="h", streak=3, sheen=8), "copper")
    img = M.new((S, S), (232, 186, 36))
    for y in range(S):
        for x in range(S):
            if ((x + y) // 6) % 2 == 0:
                img.putpixel((x, y), (28, 28, 30, 255))
    M.grime(img, 0.12, seed=15805, color=(90, 80, 60))
    M.scratches(img, n=6, seed=15806, light=0.15)
    save(img, "hazard")
    img = M.new((S, S), (255, 120, 40))
    for y in range(S):
        for x in range(S):
            if (x % 8) in (0, 7):
                img.putpixel((x, y), (200, 70, 30, 255))
    save(img, "heatlamp")
    save(M.new((S, S), (70, 44, 36)), "heatlampoff")
    # A canteen tray's red and grey plastic
    save(M.rubber(seed=15807, base=(150, 40, 36)), "trayred")
    save(M.rubber(seed=15808, base=(110, 116, 122)), "traygrey")
    # Hydroponics: the white PVC channels, their lids with a row of holes, a net pot's black mesh, the LED bars
    save(M.painted_metal(seed=15809, base=(228, 230, 226), panel=False, chips=0), "pvc")
    save(M.new((S, S), (24, 24, 26)), "netpot")
    img = M.new((S, S), (255, 120, 236))
    for x in range(0, S, 4):
        rect(img, x, 0, x, S - 1, (255, 200, 250))
    save(img, "ledbar")
    save(M.new((S, S), (60, 44, 58)), "ledbaroff")
    # The bay curtain's mesh band: white with square holes (alpha 0: a cut-out, not translucent)
    img = M.new((S, S), (232, 236, 234))
    for y in range(S):
        for x in range(S):
            if x % 4 in (1, 2) and y % 4 in (1, 2):
                img.putpixel((x, y), (0, 0, 0, 0))
    save(img, "mesh")
    cur = M.fabric(seed=15810, base=(160, 192, 186), weave="plain", contrast=6)
    M.grime(cur, 0.1, seed=15811, color=(120, 130, 120), bias="bottom")
    save(cur, "curtainr4")
    # The medical monitor: a lit screen (a flat green trace, the numbers at zero, an amber alarm box) and a dead one
    img = Image.new("RGBA", (B, B), (6, 10, 12, 255))
    d = ImageDraw.Draw(img)
    for y, col in ((10, (60, 240, 120)), (24, (80, 200, 255)), (38, (255, 230, 90))):
        d.line((3, y, 44, y), fill=col + (255,))
    d.line((3, 10, 12, 10), fill=(60, 240, 120, 255))
    d.line((12, 10, 14, 4), fill=(60, 240, 120, 255))
    d.line((14, 4, 16, 15), fill=(60, 240, 120, 255))
    d.line((16, 15, 18, 10), fill=(60, 240, 120, 255))
    draw_text(img, (47, 4, 62, 16), "0", (60, 240, 120), 9)
    draw_text(img, (47, 18, 62, 30), "--", (80, 200, 255), 9)
    draw_text(img, (47, 32, 62, 44), "--", (255, 230, 90), 9)
    rect(img, 3, 48, 40, 58, (150, 90, 10))
    draw_text(img, (4, 49, 39, 57), "ASYSTOLE", (255, 230, 180), 5, condensed=True)
    rect(img, 0, 0, B - 1, 1, (40, 44, 50))
    save(img, "medscreen-lit")
    img = Image.new("RGBA", (B, B), (16, 18, 22, 255))
    for k in range(20):
        blend(img, 12 + k, 8 + k // 2, (60, 66, 76), 0.45)
    save(img, "medscreen-dead")
    # The headwall rail: white with two gas outlets (green O2, white air), a nurse-call socket
    img = M.painted_metal(seed=15812, base=(226, 228, 228), panel=False, chips=0)
    for cx, col in ((6, (40, 160, 80)), (14, (230, 232, 232)), (22, (30, 34, 38))):
        rect(img, cx - 2, 12, cx + 2, 19, (180, 184, 188))
        M.bevel(img, (cx - 2, 12, cx + 3, 20), strength=0.2)
        rect(img, cx - 1, 14, cx + 1, 17, col)
    M.emboss_lines(img, ys=(4, 27), strength=0.18)
    save(img, "headwall")
    # Emergency lamp lenses (lit amber, dead), the breaker panel's inside (rows of breakers, one tripped with a red flag)
    img = M.new((S, S), (255, 196, 90))
    for y in range(0, S, 3):
        rect(img, 0, y, S - 1, y, (255, 214, 140))
    save(img, "emerglit")
    save(M.new((S, S), (92, 74, 50)), "emergdead")
    img = M.new((S, S), (54, 58, 62))
    for row, y in enumerate((4, 13, 22)):
        for k, x in enumerate(range(3, 29, 4)):
            rect(img, x, y, x + 2, y + 6, (200, 204, 206))
            tripped = (row, k) == (1, 3)
            rect(img, x, y + (4 if tripped else 1), x + 2, y + (5 if tripped else 2), (210, 40, 30) if tripped else (40, 44, 48))
    save(img, "breakers")
    # The bulkheads: white steel with a hazard foot, a stencil plate, the header's face with a hazard strip at its foot
    beam = load("wall-beam")
    kick = beam.copy()
    hz = load("hazard")
    kick.paste(hz.crop((0, 0, S, 12)), (0, 20))
    M.emboss_lines(kick, ys=(20,), raised=True, strength=0.25)
    save(kick, "bh-kick")
    plate = beam.copy()
    rect(plate, 7, 9, 24, 22, (40, 44, 50))
    M.bevel(plate, (7, 9, 25, 23), strength=0.25)
    for sx, sy in ((8, 10), (23, 10), (8, 21), (23, 21)):
        M.screw(plate, sx, sy)
    save(plate, "bh-plate")
    head = M.brushed_metal(seed=15813, base=(206, 211, 216), direction="h", streak=6, sheen=8)
    M.emboss_lines(head, ys=(3, 21), strength=0.2)
    head.paste(hz.crop((0, 0, S, 6)), (0, 24))
    for x in (4, 12, 20, 28):
        M.touch(head, x, 12, 0.25)
        M.touch(head, x, 13, -0.2)
    M.grime(head, 0.05, seed=15814, color=(120, 120, 116))
    save(head, "bh-head")
    img = M.new((S, S), (236, 246, 255))
    save(img, "bh-light")
    save(M.new((S, S), (110, 116, 122)), "bh-lightdead")
    # A stencilled bulkhead code plate at 64 px (one per hall line colour): "BULKHEAD" over the line's swatch
    for i, col in enumerate(LINE_COLOURS):
        img = Image.new("RGBA", (B, B), (40, 44, 50, 255))
        rect(img, 2, 2, B - 3, B - 3, (48, 54, 60))
        rect(img, 6, 6, B - 7, 20, tuple(col))
        draw_text(img, (6, 24, B - 6, 38), "BULKHEAD", (220, 228, 232), 8, condensed=True)
        draw_text(img, (6, 42, B - 6, 56), "KEEP CLEAR", (232, 186, 36), 7, condensed=True)
        save(img, f"bh-code{i}")
    # The lift's lit indicator, two halves at 64 x 64 (the arrow and "B3" in amber on black)
    img = Image.new("RGBA", (2 * B, B), (8, 6, 4, 255))
    d = ImageDraw.Draw(img)
    d.polygon([(30, 12), (46, 40), (14, 40)], fill=(255, 168, 40, 255))
    draw_text(img, (64, 6, 120, 52), "B3", (255, 168, 40), 30)
    save(img.crop((0, 0, B, B)), "liftdisp0")
    save(img.crop((B, 0, 2 * B, B)), "liftdisp1")
    # Canteen laminate (white with a fine fleck) and its aluminium edge
    lam = M.noise_hv((230, 232, 228), amp=2, seed=15815, mottle=3)
    rng = random.Random(15816)
    for _ in range(40):
        lam.putpixel((rng.randrange(S), rng.randrange(S)), (196, 198, 196, 255))
    M.scratches(lam, n=5, seed=15817, light=0.08)
    save(lam, "laminate")
    # The floor lights along the halls' feet as inset fixtures: a steel rim stepped down, a frosted lens with a bright core
    cer = load("floor-ceramic")
    for name, lens, core in (("floor-strip", (226, 238, 250), (252, 254, 255)), ("floor-stripdead", (104, 110, 116), (120, 126, 132))):
        img = cer.copy()
        rect(img, 2, 2, 29, 29, (150, 156, 162))
        M.inset(img, (2, 2, 30, 30), width=1, strength=0.3)
        rect(img, 4, 4, 27, 27, (96, 100, 106))
        rect(img, 5, 5, 26, 26, lens)
        rect(img, 8, 8, 23, 23, core)
        for k in range(5, 27, 3):
            blend(img, k, 5, (255, 255, 255), 0.3)
        for sx, sy in ((3, 3), (28, 3), (3, 28), (28, 28)):
            M.screw(img, sx, sy, slot=False)
        save(opaque(img), name)


# ======================================================================== Shapes

def faces_only(el, *keep):
    el["faces"] = {k: v for k, v in el["faces"].items() if k in keep}
    return el


def uvfull(el, *names):
    for n in names or list(el["faces"]):
        if n in el["faces"]:
            el["faces"][n]["uv"] = [0, 0, 16, 16]
    return el


def console_shape(state):
    """A console desk, its operator's side to the north: a dark plinth set back, white pedestal with a vented front,
    steel cheeks, a dark worktop with a rounded front lip, a keyboard and a trackball, a monitor on a neck and foot,
    tilted back, its screen lit (dead: dark glass), a cable down the back and a status LED."""
    lit = state != "dead"
    screen = "cscreen-" + state
    tilt = dict(rot=(-10, 0, 0), origin=(8, 12.5, 11.5))
    els = [
        box("Plinth", (2, 0, 3.5), (14, 1, 14.5), "dark"),
        box("Pedestal", (1, 1, 2.5), (15, 8, 15), {"all": "white", "front": "lockervents"}),
        box("CheekW", (0, 0, 1), (1, 9.5, 16), "steelgrey"),
        box("CheekE", (15, 0, 1), (16, 9.5, 16), "steelgrey"),
        box("Top", (1, 8, 1), (15, 9, 16), {"all": "steelgrey", "top": "epoxy"}),
        box("Lip", (1, 8.25, 0.25), (15, 9.25, 1.25), "bezel"),
        box("Keyboard", (3, 9, 2), (11.5, 9.5, 6), {"all": "bezel", "top": "keys"}, rot=(6, 0, 0), origin=(7, 9, 6),
            uv=None),
        box("BallBase", (12.25, 9, 2.5), (14.5, 9.5, 5), "bezel"),
        box("Ball", (12.85, 9.5, 3.1), (13.9, 10.2, 4.15), "ledred" if lit else "dark", glow=60 if lit else 0),
        box("Foot", (5.5, 9, 10.5), (10.5, 9.4, 14), "bezel"),
        box("Neck", (7.25, 9.4, 12), (8.75, 13.5, 13), "steelgrey"),
        box("Housing", (1.5, 12, 10.5), (14.5, 20, 12.5), "bezel", **tilt),
        box("HousingBack", (3.5, 13, 12.5), (12.5, 19, 13.5), "bezel", **tilt),
        box("Screen", (2.25, 12.75, 10.4), (13.75, 19.25, 10.5), screen, faces=("north",), glow=170 if lit else 0, **tilt),
        box("Cable", (8, 1, 15), (8.75, 12, 15.75), "dark"),
        box("Led", (12.5, 6, 2.4), (13.25, 6.75, 2.5), "ledgreen" if lit else "dark", faces=("north",), glow=200 if lit else 0),
    ]
    els[13]["faces"]["north"]["uv"] = [0, 0, 16, 10]
    els[6]["faces"]["up"]["uv"] = [0, 0, 16, 8]
    return write_shape("l15-console-" + state, els, {k: T(k) for k in
                       ("dark", "white", "lockervents", "steelgrey", "epoxy", "bezel", "keys", "ledred", "ledgreen", screen)})


def dock_shape(part, lit):
    """The robot charging dock, against a wall to the south, open to the north (round 4): a back plate with an inset
    panel, chamfered white cheeks with a status strip, a charging pad with guide rails and copper studs, contact arms
    reaching the robot's shoulders, a conduit up the side; the hood (upper) with a lit edge, the plate, a charge
    display and the lamp. The docked Robo-Man is the creature's own model, its eyes lit while the dock has power."""
    lamp = "docklit" if lit else "dockdead"
    g = 200 if lit else 0
    tex = {k: T(k) for k in ("steelgrey", "white", "dark", "brushed", "copper", "hazard", lamp, "dockplate", "lockerdoor", "bezel",
                             "ledamber" if lit else "dark")}
    els = [box("Back", (1, 0, 14.5), (15, 16, 16), {"all": "steelgrey", "front": "lockerdoor"}),
           box("CheekW", (0, 0, 9.5), (1.5, 16 if part == "lower" else 12, 16), "white"),
           box("CheekE", (14.5, 0, 9.5), (16, 16 if part == "lower" else 12, 16), "white"),
           box("ChamferW", (0.35, 0, 8.6), (1.35, 16 if part == "lower" else 12, 10.6), "brushed",
               rot=(0, 45, 0), origin=(0.85, 8, 9.6)),
           box("ChamferE", (14.65, 0, 8.6), (15.65, 16 if part == "lower" else 12, 10.6), "brushed", rot=(0, -45, 0), origin=(15.15, 8, 9.6)),
           box("StripW", (1.5, 1 if part == "lower" else 0, 12.5), (1.75, 16 if part == "lower" else 11, 13.5), lamp, glow=g,
               faces=("east",)),
           box("StripE", (14.25, 1 if part == "lower" else 0, 12.5), (14.5, 16 if part == "lower" else 11, 13.5), lamp, glow=g,
               faces=("west",)),
           box("Conduit", (14.5, 0, 15.25), (15.5, 16, 16.25), "dark")]
    extra = None
    if part == "lower":
        els += [box("Pad", (1.5, 0, 3), (14.5, 0.6, 14.5), {"all": "dark", "top": "hazard"}),
                box("PadInner", (3, 0.6, 4.5), (13, 0.7, 13.5), "steelgrey", faces=("up",)),
                box("RailW", (2, 0.6, 3.5), (3, 1.4, 14.5), "brushed"),
                box("RailE", (13, 0.6, 3.5), (14, 1.4, 14.5), "brushed"),
                box("StudW", (5, 0.6, 9), (6.5, 1.1, 10.5), "copper"),
                box("StudE", (9.5, 0.6, 9), (11, 1.1, 10.5), "copper"),
                # The contact arms: from the back plate to the robot's shoulders, a sprung pad at each end
                box("ArmW", (3.25, 11, 11.5), (4.25, 12, 14.5), "brushed"),
                box("ArmE", (11.75, 11, 11.5), (12.75, 12, 14.5), "brushed"),
                box("SpringW", (3.4, 11.15, 12.5), (4.1, 11.85, 13.5), "copper"),
                box("SpringE", (11.9, 11.15, 12.5), (12.6, 11.85, 13.5), "copper"),
                box("PadW", (3, 10.5, 10.9), (4.5, 12.5, 11.5), "copper"),
                box("PadE", (11.5, 10.5, 10.9), (13, 12.5, 11.5), "copper")]
        robot = json.load(open(os.path.join(ROOT, "assets", "backrooms", "shapes", "entity", "roboman.json"), encoding="utf-8"))
        flat = []

        def walk(es, ox, oy, oz):
            for e in es:
                (x1, y1, z1), (x2, y2, z2) = e["from"], e["to"]
                ax, ay, az = ox + x1, oy + y1, oz + z1
                f = e["faces"]
                faces = {k: dict(v) for k, v in {"east": f.get("north"), "south": f.get("east"), "west": f.get("south"),
                                                  "north": f.get("west"), "up": f.get("up"), "down": f.get("down")}.items() if v}
                if lit and (e["name"].startswith("Eye") or e["name"] == "Bulb"):
                    for v in faces.values():
                        v["glow"] = 160
                flat.append({"name": "Robot" + e["name"], "from": [16 - (oz + z2), ay + 0.75, ax], "to": [16 - az, oy + y2 + 0.75, ox + x2],
                             "faces": faces})
                walk(e.get("children", []), ax, ay, az)
        walk(robot["elements"], 0, 0, 0)
        els += flat
        tex["skin"] = "backrooms:entity/roboman"
        extra = {"textureSizes": {"skin": [robot.get("textureWidth", 64), robot.get("textureHeight", 64)]}}
    else:
        els += [box("Hood", (0, 12, 5.5), (16, 16, 16), "white"),
                box("HoodLip", (0.5, 11.5, 5), (15.5, 12, 6.5), "brushed"),
                box("HoodLight", (1.5, 11.25, 6.5), (14.5, 11.5, 9), lamp, faces=("down",), glow=g),
                uvfull(box("Plate", (5, 12.5, 5.25), (11, 15.5, 5.5), "dockplate", faces=("north",))),
                box("Display", (1.5, 12.75, 5.25), (4.25, 15.25, 5.5), {"all": "bezel", "north": "ledamber" if lit else "dark"},
                    glow=90 if lit else 0),
                box("Lamp", (12, 13, 4.75), (13.5, 14.5, 5.5), lamp, glow=255 if lit else 0),
                box("LampHood", (11.75, 14.5, 4.5), (13.75, 14.9, 5.5), "steelgrey")]
    tex["brushed"] = T("brushed")
    return write_shape(f"l15-dock-{part}-{'lit' if lit else 'dead'}", els, tex, extra)


def seat_shape(kind):
    """A lecture seat facing north (round 4): cast side standards with a foot and an arm pad, a cushion with a front
    roll on a shell, a back in two pitches on its shell, a tablet folded down on its pivot by the right arm, the seat's
    number on the back. hi: on a half step (the step under it, everything 8 up)."""
    up = 8 if kind == "hi" else 0
    els = []
    if up:
        els.append(box("Step", (0, 0, 0), (16, 8, 16), {"top": "carpet", "side": "dark"}))
        els.append(box("Nosing", (0, 7, -0.01), (16, 8, 0.5), "steelgrey", faces=("north", "up")))
    for side, x in (("W", 0.5), ("E", 14.5)):
        els += [box(f"Leg{side}", (x, up, 9), (x + 1, up + 9, 11.5), "steelgrey"),
                box(f"Foot{side}", (x - 0.25, up, 6.5), (x + 1.25, up + 0.5, 13.5), "steelgrey"),
                box(f"ArmPost{side}", (x, up + 5, 5), (x + 1, up + 9, 6), "steelgrey"),
                box(f"Arm{side}", (x - 0.25, up + 9, 4), (x + 1.25, up + 10, 12.5), "epoxy")]
    back = dict(rot=(-7, 0, 0), origin=(8, up + 7, 13))
    back2 = dict(rot=(-14, 0, 0), origin=(8, up + 12, 13.6))
    els += [
        box("Shell", (2, up + 4.25, 4), (14, up + 5, 12), "steelgrey"),
        box("Cushion", (2, up + 5, 4), (14, up + 7, 12), "seatcloth"),
        box("Roll", (2, up + 5.5, 3.25), (14, up + 7.25, 4.25), "seatcloth"),
        box("BackLow", (2, up + 7, 12), (14, up + 12, 13.6), "seatcloth", **back),
        box("BackHigh", (2.25, up + 12, 12.4), (13.75, up + 16.5, 13.8), "seatcloth", **back2),
        box("BackShell", (1.75, up + 7, 13.6), (14.25, up + 12, 14.2), "steelgrey", **back),
        box("BackShell2", (2, up + 12, 13.8), (14, up + 16.5, 14.4), "steelgrey", **back2),
        uvfull(box("Number", (7, up + 14.5, 14.45), (9, up + 15.5, 14.5), "brushed", faces=("south",)), "south"),
        box("Pivot", (15.25, up + 8, 9.5), (16, up + 9, 11), "dark"),
        box("Tablet", (15.4, up + 1.5, 4.5), (15.9, up + 8.75, 11), "epoxy"),
    ]
    els[-3]["faces"]["south"]["uv"] = [0, 0, 4, 2]
    return write_shape("l15-seat-" + kind, els, {"carpet": T("floor-carpet"), "dark": T("dark"), "steelgrey": T("steelgrey"),
                                                 "seatcloth": T("seatcloth"), "epoxy": T("epoxy"), "brushed": T("brushed")})


def riser_shape(kind):
    h = 8 if kind == "half" else 16
    els = [box("Step", (0, 0, 0), (16, h, 16), {"top": "carpet", "side": "dark"})]
    if kind == "half":
        els.append(box("Nosing", (0, h - 1, -0.01), (16, h, 0.5), "steelgrey", faces=("north", "up")))
        # The aisle's step light, a small lens in the riser's face
        els.append(box("StepLight", (6.5, 3, -0.1), (9.5, 4.25, 0), "bh-light", faces=("north",), glow=180))
    return write_shape("l15-riser-" + kind, els, {"carpet": T("floor-carpet"), "dark": T("dark"), "steelgrey": T("steelgrey"),
                                                  "bh-light": T("bh-light")})


def serve_shape(kind):
    """The serving line (round 4), the customer's side to the north: a stainless counter on a kick, its front in panels,
    a worktop with a lip; a tubular tray slide on brackets; on top two wells with steel pans and a ladle, or a stack of
    trays and a cutlery bin, or the till with its screen and a cash drawer; over the wells and trays a gantry of two
    posts and a shelf with a heat lamp under it, and an angled sneeze guard of glass in a steel frame."""
    els = [
        box("Body", (0, 1, 3), (16, 12.5, 16), {"all": "sinksteel", "front": "lockerdoor"}),
        box("Kick", (0.5, 0, 3.5), (15.5, 1, 15.5), "dark"),
        box("Top", (0, 12.5, 2.5), (16, 13.5, 16), "sinksteel"),
        box("Lip", (0, 12.75, 2.25), (16, 13.75, 2.75), "brushed"),
        box("BracketW", (2, 10.25, 0.5), (2.75, 11.25, 3), "brushed"),
        box("BracketE", (13.25, 10.25, 0.5), (14, 11.25, 3), "brushed"),
    ]
    for i, z in enumerate((0.25, 1.05, 1.85)):
        els.append(box(f"Slide{i}", (0, 11.25, z), (16, 11.85, z + 0.6), "brushed"))
    if kind == "wells":
        for i, x in enumerate((1.25, 8.75)):
            els += [box(f"Well{i}", (x, 13.45, 4.5), (x + 6, 13.55, 13), "dark", faces=("up",)),
                    box(f"PanN{i}", (x, 13.5, 4.5), (x + 6, 14, 5), "brushed"),
                    box(f"PanS{i}", (x, 13.5, 12.5), (x + 6, 14, 13), "brushed"),
                    box(f"PanW{i}", (x, 13.5, 5), (x + 0.5, 14, 12.5), "brushed"),
                    box(f"PanE{i}", (x + 5.5, 13.5, 5), (x + 6, 14, 12.5), "brushed"),
                    box(f"Divider{i}", (x + 2.8, 13.5, 5), (x + 3.2, 13.9, 12.5), "brushed")]
        els += [box("LadleBowl", (3, 13.55, 6), (5, 14.3, 8), "brushed"),
                box("LadleHandle", (3.75, 14.2, 8), (4.25, 14.6, 13.5), "brushed", rot=(-28, 0, 0), origin=(4, 14.3, 8))]
    elif kind == "trays":
        for k in range(6):
            t = "trayred" if k % 3 != 1 else "traygrey"
            els.append(box(f"Tray{k}", (2.5 + 0.25 * (k % 2), 13.5 + k * 0.55, 4.5), (11 + 0.25 * (k % 2), 14 + k * 0.55, 12.5), t))
        els += [box("Bin", (12, 13.5, 8), (15, 15.5, 13), {"all": "brushed", "top": "dark"}),
                box("BinDiv", (13.4, 13.5, 8), (13.6, 15.6, 13), "brushed")]
    else:
        tilt = dict(rot=(-18, 0, 0), origin=(8, 17, 11.5))
        els += [box("Till", (4, 13.5, 6), (12, 16, 13), {"all": "bezel", "top": "keys"}),
                box("Drawer", (4.25, 13.6, 5.75), (11.75, 15, 6), "bezel", faces=("north",)),
                box("TillNeck", (7.25, 16, 11), (8.75, 17.5, 12), "steelgrey"),
                box("TillScreen", (4.5, 17, 10.75), (11.5, 21.5, 12), {"all": "bezel"}, **tilt),
                box("TillGlass", (5, 17.5, 10.65), (11, 21, 10.75), "cscreen-dead", faces=("north",), **tilt),
                box("Reader", (12.5, 13.5, 4), (14.5, 15.5, 5.5), "bezel", rot=(20, 0, 0), origin=(13.5, 13.5, 5))]
        els[-2]["faces"]["north"]["uv"] = [0, 0, 16, 10]
    if kind != "till":
        guard = dict(rot=(-22, 0, 0), origin=(8, 22.5, 4.25))
        els += [box("PostW", (0.25, 13.5, 6), (1, 24, 6.75), "brushed"),
                box("PostE", (15, 13.5, 6), (15.75, 24, 6.75), "brushed"),
                box("Shelf", (0, 23.5, 3), (16, 24.25, 10), "sinksteel"),
                box("ShelfLip", (0, 23.25, 2.75), (16, 24.5, 3.25), "brushed"),
                box("HeatLamp", (1.5, 23, 5), (14.5, 23.5, 8.5), {"all": "dark", "down": "heatlampoff"}),
                uvfull(box("Guard", (1, 16, 4.1), (15, 22.5, 4.4), "guardcut", faces=("north", "south"), **guard)),
                box("GuardRail", (1, 22.25, 3.75), (15, 22.75, 4.75), "brushed", **guard),
                box("GuardEdge", (1, 15.75, 3.75), (15, 16.25, 4.75), "brushed", **guard)]
    return write_shape("l15-serve-" + kind, els, {k: T(k) for k in ("sinksteel", "lockerdoor", "dark", "brushed", "trayred", "traygrey",
                                                                     "bezel", "keys", "steelgrey", "cscreen-dead", "guardcut",
                                                                     "heatlamp", "heatlampoff")})


def growrack_shape(part, lit):
    """A hydroponics rack (round 4), its aisle side to the north: four posts (feet on the lower part), a frame under
    each of two levels, three channels on each with net pots and small dead plants, a feed line along the back with a
    dripper into each channel, a return pipe under the level, LED bars in housings over each level (lit magenta, off)."""
    led = "ledbar" if lit else "ledbaroff"
    rng = random.Random(15820 + (part == "upper") * 7 + lit)
    els = []
    for x in (0.5, 14.5):
        for z in (2, 13):
            els.append(box(f"Post{x}{z}", (x, 0, z), (x + 1, 16, z + 1), "brushed"))
            if part == "lower":
                els.append(box(f"Foot{x}{z}", (x - 0.25, 0, z - 0.25), (x + 1.25, 0.5, z + 1.25), "dark"))
    for i, y in enumerate((1, 9)):
        els += [box(f"RailN{i}", (0.5, y - 1, 2), (15.5, y, 3), "brushed"),
                box(f"RailS{i}", (0.5, y - 1, 13), (15.5, y, 14), "brushed"),
                box(f"Cross{i}", (7.5, y - 0.75, 3), (8.5, y - 0.25, 13), "brushed")]
        for c, zc in enumerate((3.5, 7, 10.5)):
            els.append(box(f"Chan{i}{c}", (0.75, y, zc), (15.25, y + 1.25, zc + 2.25), "pvc"))
            for p, px in enumerate((3, 8, 13)):
                if rng.random() < 0.15:
                    continue
                cz = zc + 1.125
                els.append(box(f"Pot{i}{c}{p}", (px - 0.6, y + 1.25, cz - 0.6), (px + 0.6, y + 1.45, cz + 0.6), "netpot"))
                h = rng.uniform(1.2, 3.2)
                lean = rng.uniform(-14, 14)
                els.append(box(f"Stalk{i}{c}{p}", (px - 0.15, y + 1.45, cz - 0.15), (px + 0.15, y + 1.45 + h, cz + 0.15), "deadstalk",
                               rot=(lean, 0, rng.uniform(-10, 10)), origin=(px, y + 1.45, cz)))
                if rng.random() < 0.75:
                    ang = rng.uniform(0, 360)
                    ly = y + 1.45 + h * rng.uniform(0.5, 0.9)
                    els.append(box(f"Leaf{i}{c}{p}", (px, ly, cz - 0.3), (px + 1.3, ly + 0.1, cz + 0.3), "deadplant",
                                   rot=(0, ang - 180, -rng.uniform(25, 60)), origin=(px, ly, cz)))
        els += [box(f"Feed{i}", (0, y + 2.75, 13.25), (16, y + 3.35, 13.85), "pvc"),
                box(f"Return{i}", (0, y - 2.1, 12.5), (16, y - 1.4, 13.2), "pipe")]
        for c, zc in enumerate((3.5, 7, 10.5)):
            els.append(box(f"Drip{i}{c}", (1.5, y + 1.25, zc + 1), (1.75, y + 2.75, zc + 1.25), "dark"))
        ly = 7.5 if i == 0 else 15.5
        for b, z in enumerate((5, 10)):
            els += [box(f"Housing{i}{b}", (1.5, ly - 0.1, z - 0.4), (14.5, ly + 0.4, z + 1.4), "brushed"),
                    box(f"Led{i}{b}", (1.75, ly - 0.35, z - 0.15), (14.25, ly - 0.1, z + 1.15), led, faces=("down", "north", "south"),
                        glow=230 if lit else 0)]
        els.append(box(f"LedCable{i}", (14.5, ly, 5.5), (15, ly + 0.3, 10.5), "dark"))
    if part == "upper":
        els.append(box("Top", (0.5, 15.5, 2), (15.5, 16, 14), "brushed", faces=("up", "north", "south", "east", "west")))
    return write_shape(f"l15-growrack-{part}-{'lit' if lit else 'off'}", els,
                       {k: T(k) for k in ("brushed", "dark", "pvc", "netpot", "deadplant", "deadstalk", "pipe", led)})


def curtain_shape(part):
    """A medical bay's curtain (round 4) along the north edge of the block: upper, a ceiling track with end caps and
    gliders, rods up to the ceiling plate a block above, a mesh band and the pleats' tops; lower, the pleats down to a
    hem a hand above the floor. Pleats are strips turned in and out about their middles."""
    els = []
    y0, y1 = (-11, 16) if part == "lower" else (0, 11)
    rng = random.Random(15830 + (part == "lower"))
    for i in range(8):
        a = 32 if i % 2 == 0 else -32
        drop = rng.uniform(0, 0.8) if part == "lower" else 0
        els.append(box(f"Pleat{i}", (i * 2 - 0.15, y0 + drop, 0.75), (i * 2 + 2.15, y1, 1.15), "curtainr4",
                       rot=(0, a, 0), origin=(i * 2 + 1, 8, 0.95)))
    if part == "upper":
        els += [box("Mesh", (0, 11, 0.8), (16, 14.25, 1.1), "mesh"),
                box("Track", (0, 14.75, 0.25), (16, 16, 1.65), "brushed"),
                box("TrackSlot", (0, 14.6, 0.75), (16, 14.75, 1.15), "dark", faces=("down",))]
        for x in range(1, 16, 2):
            els.append(box(f"Glider{x}", (x - 0.3, 14.2, 0.7), (x + 0.3, 14.75, 1.2), "dark"))
        for x in (3.75, 11.75):
            els += [box(f"Rod{x}", (x, 16, 0.7), (x + 0.5, 31.6, 1.2), "brushed"),
                    box(f"Plate{x}", (x - 0.75, 31.6, -0.05), (x + 1.25, 32, 1.95), "brushed")]
    return write_shape("l15-curtain-" + part, els, {k: T(k) for k in ("curtainr4", "mesh", "brushed", "dark")})


def hangsign_shape(part, axis):
    """One of the three blocks of a hanging sign (round 4): the glowing panel in a steel channel frame, its lower edge
    a lit strip, end caps on the outer blocks; rods with ceiling plates on the outer blocks, a cable on the middle one.
    Modelled across x (we) and turned for ns, the faces kept as round 3 had them (front/back by axis)."""
    els = [box("Panel", (0, 4, 7.5), (16, 14, 8.5), {"north": "back", "south": "front", "up": "rim", "down": "rim", "east": "rim", "west": "rim"}),
           box("FrameTop", (0, 14, 7.15), (16, 14.75, 8.85), "frame"),
           box("FrameBot", (0, 3.25, 7.15), (16, 4, 8.85), {"all": "frame", "down": "edge"}),
           box("EdgeN", (0, 3.5, 7.05), (16, 3.9, 7.15), "edge", faces=("north",)),
           box("EdgeS", (0, 3.5, 8.85), (16, 3.9, 8.95), "edge", faces=("south",))]
    for e in els[:1]:
        for f in e["faces"].values():
            f["uv"] = [0, 0, 16, 16]
    if part == 0:
        els.append(box("CapW", (-0.4, 3.25, 7.15), (0.35, 14.75, 8.85), "frame"))
    if part == 2:
        els.append(box("CapE", (15.65, 3.25, 7.15), (16.4, 14.75, 8.85), "frame"))
    if part != 1:
        rx = 4 if part == 0 else 12
        els += [box("Rod", (rx - 0.25, 14.75, 7.75), (rx + 0.25, 16, 8.25), "frame"),
                box("CeilPlate", (rx - 1, 15.7, 7), (rx + 1, 16, 9), "frame"),
                box("Clamp", (rx - 0.6, 14.6, 7.4), (rx + 0.6, 15.1, 8.6), "frame")]
    else:
        els.append(box("Cable", (7.9, 14.75, 7.9), (8.1, 16, 8.1), "rim"))
    if axis == "ns":
        swap = {"north": "west", "south": "east", "west": "north", "east": "south", "up": "up", "down": "down"}
        out = []
        for e in els:
            e = json.loads(json.dumps(e))
            (x1, y1, z1), (x2, y2, z2) = e["from"], e["to"]
            e["from"], e["to"] = [z1, y1, x1], [z2, y2, x2]
            e["faces"] = {swap[k]: v for k, v in e["faces"].items()}
            if e["name"] == "Panel":
                # round 3: ns faces east = back, west = front
                e["faces"]["east"] = dict(e["faces"]["east"], texture="#back")
                e["faces"]["west"] = dict(e["faces"]["west"], texture="#front")
            out.append(e)
        els = out
    return els


def panel_els(front="wall"):
    """The wall block behind a panel model: a full cube, its front face as given."""
    return [box("Wall", (0, 0, 0), (16, 16, 16), {"all": "wall", "north": front})]


PANEL_KINDS = []


def panel_shapes():
    """l15-panel's shapes, each a white wall block with a model on its north face; returns {kind: (shape, light)}."""
    out = {}

    def add(kind, els, tex, light=None, extra=None):
        tex = dict(tex)
        tex.setdefault("wall", T("wall-panel"))
        out[kind] = (write_shape("l15-panel-" + kind, els, tex, extra), light)

    # The extinguisher: the detail kit's own model (concretedeco-extinguisher), on 15's white panel
    src = json.load(open(os.path.join(ASSETS, "shapes", "block", "detail", "concretedeco-extinguisher.json"), encoding="utf-8"))
    tex = dict(src["textures"])
    tex.pop("concretewall", None)
    els = json.loads(json.dumps(src["elements"]))
    for e in els:
        for f in e["faces"].values():
            if f.get("texture") == "#concretewall":
                f["texture"] = "#wall"
    add("ext", els, tex, extra={k: v for k, v in src.items() if k in ("textureWidth", "textureHeight", "textureSizes")})

    # The ESCAPE panel, dead (the live one is the links' own): a bezel standing off the panel, the yellow collar and the
    # red mushroom button standing out, a key switch, the green lamp
    els = panel_els("deco-escape") + [
        box("BezelT", (1.5, 14, -0.6), (14.5, 14.75, 0), "bezel"),
        box("BezelB", (1.5, 1.25, -0.6), (14.5, 2, 0), "bezel"),
        box("BezelW", (14, 2, -0.6), (14.75, 14, 0), "bezel"),
        box("BezelE", (1.25, 2, -0.6), (2, 14, 0), "bezel"),
        box("Collar", (5.4, 3.6, -0.7), (10.6, 9.2, 0), "yellowcollar"),
        box("Button", (6.1, 4.3, -1.9), (9.9, 8.5, -0.7), "redbutton"),
        box("ButtonCap", (6.6, 4.8, -2.3), (9.4, 8.0, -1.9), "redbutton"),
        box("Lamp", (3.3, 3.7, -0.5), (4.5, 4.9, 0), "dark"),
        box("Key", (11.6, 3.8, -0.7), (12.8, 5.0, 0), "brushed"),
        box("KeySlot", (12.05, 4.1, -0.75), (12.35, 4.7, -0.7), "dark", faces=("north",)),
    ]
    add("escape", els, {"deco-escape": T("deco-escape"), "bezel": T("bezel"), "yellowcollar": T("yellowcollar"),
                        "redbutton": T("redbutton"), "dark": T("dark"), "brushed": T("brushed")})

    # The lift: each leaf block (l: outer edge at x 16 as seen from the hall, r: at x 0; rows 0-2 from the floor) its
    # leaf recessed 1.5 into the wall behind a proud brushed-steel portal (jamb on the outer edge, the head over row 2,
    # a sill at the foot of row 0); the indicator over the doors as a lit display in the portal's head; the call panel
    for side in ("l", "r"):
        for row in range(3):
            els = [box("Body", (0, 0, 1.5), (16, 16, 16), {"all": "wall", "north": f"sign-lift{side}{row}"})]
            uvfull(els[0], "north")
            jx = (13.5, 16.75) if side == "l" else (-0.75, 2.5)
            els.append(box("Jamb", (jx[0], 0, -1), (jx[1], 16, 1.5), "brushedv"))
            els.append(box("JambStep", (jx[0] + (0 if side == "l" else 2.25), 0, -1.25), (jx[0] + (1 if side == "l" else 3.25), 16, -1),
                           "bezel", faces=("north",)))
            if row == 0:
                els.append(box("Sill", (0, -0.01, -1.5), (16, 0.35, 1.5), "brushed"))
                els.append(box("SillGroove", (0, 0.35, 0.4), (16, 0.4, 0.8), "dark", faces=("up",)))
            if row == 2:
                els.append(box("Head", (0, 14.25, -1), (16, 16, 1.5), "brushed"))
            add(f"lift{side}{row}", els, {f"sign-lift{side}{row}": T(f"sign-lift{side}{row}"), "brushedv": T("brushedv"),
                                          "brushed": T("brushed"), "bezel": T("bezel"), "dark": T("dark")})
    for half in (0, 1):
        els = panel_els() + [box("PortalHead", (-0.75 if half else 0, 0, -1), (16 if half else 16.75, 4, 0), "brushed")]
        dx = (0, 7) if half == 0 else (9, 16)
        els += [box("DispHousing", (dx[0], 5.5, -1.1), (dx[1], 11.5, 0), "bezel"),
                uvfull(box("Disp", (dx[0] + 0.5, 6, -1.2), (dx[1] - 0.5, 11, -1.1), f"liftdisp{half}", faces=("north",), glow=220), "north")]
        add(f"liftind{half}", els, {"brushed": T("brushed"), "bezel": T("bezel"), f"liftdisp{half}": T(f"liftdisp{half}")})
    els = panel_els() + [
        box("Plate", (5, 2.5, -0.5), (11, 13.5, 0), "brushedv"),
        box("BtnUpRing", (6.75, 8.75, -0.8), (9.25, 11.25, -0.5), "brushed"),
        box("BtnUp", (7.25, 9.25, -1.05), (8.75, 10.75, -0.8), "ledamber", glow=220),
        box("BtnDnRing", (6.75, 4.75, -0.8), (9.25, 7.25, -0.5), "brushed"),
        box("BtnDn", (7.25, 5.25, -1.05), (8.75, 6.75, -0.8), "bezel"),
        box("Braille", (7, 3.25, -0.6), (9, 3.75, -0.5), "dark"),
    ]
    add("liftcall", els, {"brushedv": T("brushedv"), "brushed": T("brushed"), "ledamber": T("ledamber"), "bezel": T("bezel"), "dark": T("dark")})

    # The wall displays (dead, the radar, the three views of elsewhere): the picture on the panel framed by a bezel that
    # stands off the wall, a chin with a power LED
    for kind, (x0, x1, y0, y1), glow, lt in (("display", (1.5, 14.5, 4, 13), 0, None), ("radar", (1, 15, 2.5, 14), 60, [24, 4, 4]),
                                             ("view0", (1, 15, 3, 13.5), 60, [10, 3, 4]), ("view1", (1, 15, 3, 13.5), 50, [36, 2, 3]),
                                             ("view2", (1, 15, 3, 13.5), 60, [9, 4, 4])):
        els = [box("Body", (0, 0, 0), (16, 16, 16), {"all": "wall", "north": "deco-" + kind})]
        els[0]["faces"]["north"]["uv"] = [0, 0, 16, 16]
        if glow:
            els[0]["faces"]["north"]["glow"] = glow
        els += [box("BezelT", (x0 - 0.5, y1, -0.7), (x1 + 0.5, y1 + 0.75, 0), "bezel"),
                box("BezelB", (x0 - 0.5, y0 - 1.25, -0.7), (x1 + 0.5, y0, 0), "bezel"),
                box("BezelW", (x0 - 0.5, y0, -0.7), (x0 + 0.25, y1, 0), "bezel"),
                box("BezelE", (x1 - 0.25, y0, -0.7), (x1 + 0.5, y1, 0), "bezel"),
                box("Led", (x0 + 0.75, y0 - 0.9, -0.8), (x0 + 1.4, y0 - 0.4, -0.7), "ledgreen" if glow else "dark", faces=("north",),
                    glow=200 if glow else 0)]
        add(kind, els, {"deco-" + kind: T("deco-" + kind), "bezel": T("bezel"), "ledgreen": T("ledgreen"), "dark": T("dark")}, light=lt)

    # The halls' tall wall lights (two blocks: lower, upper; lit-looking, giving light (on), dead): the lens in a white
    # steel housing standing off the wall, a reveal round it, the fixing screws
    for kind, tex_, part, glow in (("lamplower", "deco-lamplower", "lower", 160), ("lampupper", "deco-lampupper", "upper", 160),
                                   ("lampon", "deco-lampupper", "upper", 160), ("lamplowerdead", "deco-lamplowerdead", "lower", 0),
                                   ("lampupperdead", "deco-lampupperdead", "upper", 0)):
        els = [box("Body", (0, 0, 0), (16, 16, 16), {"all": "wall", "north": tex_})]
        els[0]["faces"]["north"]["uv"] = [0, 0, 16, 16]
        if glow:
            els[0]["faces"]["north"]["glow"] = glow
        lo, hi = (1, 16) if part == "lower" else (0, 15)
        els += [box("HousingW", (13, lo, -1.25), (14.25, hi, 0), "whitegloss"),
                box("HousingE", (1.75, lo, -1.25), (3, hi, 0), "whitegloss"),
                box("RevealW", (12.75, lo, -1.3), (13, hi, -1.25), "bezel", faces=("north",)),
                box("RevealE", (3, lo, -1.3), (3.25, hi, -1.25), "bezel", faces=("north",))]
        if part == "lower":
            els += [box("HousingB", (1.75, 0, -1.25), (14.25, 1, 0), "whitegloss"),
                    box("Screw0", (2.1, 0.3, -1.35), (2.6, 0.8, -1.25), "bezel", faces=("north",)),
                    box("Screw1", (13.4, 0.3, -1.35), (13.9, 0.8, -1.25), "bezel", faces=("north",))]
        else:
            els += [box("HousingT", (1.75, 15, -1.25), (14.25, 16, 0), "whitegloss"),
                    box("Screw0", (2.1, 15.2, -1.35), (2.6, 15.7, -1.25), "bezel", faces=("north",)),
                    box("Screw1", (13.4, 15.2, -1.35), (13.9, 15.7, -1.25), "bezel", faces=("north",))]
        add(kind, els, {tex_: T(tex_), "whitegloss": T("whitegloss"), "bezel": T("bezel")},
            light=[34, 1, 12] if kind == "lampon" else None)

    # The halls' tags on the band every 32 blocks (round 4): the band in its line's colour behind, a dark plate standing
    # off it with the hall's name and a small arrow, screwed at its corners
    from gen_15_r3 import HALLS
    for c in range(len(LINE_COLOURS)):
        for n in range(len(HALLS)):
            els = [box("Body", (0, 0, 0), (16, 16, 16), {"all": "wall", "north": f"sign-band{c}"})]
            els[0]["faces"]["north"]["uv"] = [0, 0, 16, 16]
            els += [uvfull(box("Plate", (3, 4.5, -0.5), (13, 11.5, 0), {"all": "bezel", "north": f"tag{n}"}), "north"),
                    box("Screw0", (3.5, 10.5, -0.6), (4, 11, -0.5), "brushed", faces=("north",)),
                    box("Screw1", (12, 10.5, -0.6), (12.5, 11, -0.5), "brushed", faces=("north",)),
                    box("Screw2", (3.5, 5, -0.6), (4, 5.5, -0.5), "brushed", faces=("north",)),
                    box("Screw3", (12, 5, -0.6), (12.5, 5.5, -0.5), "brushed", faces=("north",))]
            add(f"tag{c}{n}", els, {f"sign-band{c}": T(f"sign-band{c}"), "bezel": T("bezel"), f"tag{n}": T(f"tag{n}"), "brushed": T("brushed")})

    # The surround of Level 14's MEDICAL CENTER door in a medical bay's wall (the block over the door; the door is Level
    # 14's own): a white steel portal on both faces, its jambs reaching down past the door's sides, a lit strip under the
    # head and a green cross lamp over the door (dead in the dark)
    for lit in (True, False):
        g = 220 if lit else 0
        strip = "bh-light" if lit else "bh-lightdead"
        cross = "medcross" if lit else "medcrossdead"
        side = [box("Head", (-1.5, 0, -1.25), (17.5, 2.5, 0), "whitegloss"),
                box("HeadStrip", (0, -0.1, -1), (16, 0, -0.25), strip, faces=("down",), glow=g),
                box("JambW", (16, -32, -1.25), (17.5, 0, 0), "whitegloss"),
                box("JambE", (-1.5, -32, -1.25), (0, 0, 0), "whitegloss"),
                box("JambStripW", (16.25, -31, -1.3), (16.6, -1, -1.25), strip, faces=("north",), glow=g),
                box("JambStripE", (-0.6, -31, -1.3), (-0.25, -1, -1.25), strip, faces=("north",), glow=g),
                uvfull(box("Cross", (6.5, 4, -0.9), (9.5, 7, 0), {"all": "whitegloss", "north": cross}, glow=g), "north")]
        from modelkit import turn
        els = panel_els() + side + [dict(e, name=e["name"] + "S") for e in turn(side, 2)]
        add("medhead" + ("lit" if lit else "dead"), els, {"whitegloss": T("whitegloss"), strip: T(strip), cross: T(cross)},
            light=[23, 4, 6] if lit else None)

    # The big display's bezel (three wide, two high: row 0 the lower, i 0 the left as seen, its outer edge at x 16)
    for row in range(2):
        for i in range(3):
            els = [box("Body", (0, 0, 0), (16, 16, 16), {"all": "wall", "north": f"sign-big{row}{i}"}, glow=0)]
            uvfull(els[0], "north")
            els[0]["faces"]["north"]["glow"] = 90
            if row == 0:
                els.append(box("BezelB", (0, 0, -0.75), (16, 1, 0), "bezel"))
            else:
                els.append(box("BezelT", (0, 15, -0.75), (16, 16, 0), "bezel"))
                els.append(box("Mount", (6, 16, 0), (10, 16.01, 0.01), "bezel", faces=("north",)))
            if i == 0:
                els.append(box("BezelL", (15, 0, -0.75), (16, 16, 0), "bezel"))
            if i == 2:
                els.append(box("BezelR", (0, 0, -0.75), (1, 16, 0), "bezel"))
            if row == 0 and i == 1:
                els.append(box("Logo", (6.5, 0.25, -0.8), (9.5, 0.75, -0.75), "brushed", faces=("north",)))
            add(f"big{row}{i}", els, {f"sign-big{row}{i}": T(f"sign-big{row}{i}"), "bezel": T("bezel"), "brushed": T("brushed")})

    # The bulkheads' jambs (rows 1-5 from the floor; 5 the top, its knee brace reaching under the header): a white steel
    # post standing 3 off the wall, its edges stepped; a hazard foot; a code plate in the hall line's colour; a status
    # lamp; the etched marks on some (the lore's symbols on the beams)
    for row in range(1, 6):
        for etched in (False, True):
            front = "bh-kick" if row == 1 else ("wall-etched" if etched else "wall-beam")
            els = panel_els() + [
                box("Post", (1, 0, -3), (15, 16, 0), {"all": "wall-beam", "north": front}),
                box("StepW", (0, 0, -2), (1, 16, 0), "brushedv"),
                box("StepE", (15, 0, -2), (16, 16, 0), "brushedv"),
            ]
            if row == 3:
                els.append(box("Lamp", (7, 12, -3.5), (9, 13.5, -3), "ledgreen", glow=200))
                els.append(box("LampHood", (6.75, 13.5, -3.75), (9.25, 13.9, -3), "bezel"))
            if row == 5:
                els += [box("Knee", (1, 9, -6), (15, 16, -3), {"all": "wall-beam", "down": "bh-head"}),
                        box("Knee2", (1, 12.5, -8.5), (15, 16, -6), "wall-beam")]
            k = f"jamb{row}{'e' if etched else ''}"
            add(k, els, {"wall-beam": T("wall-beam"), "wall-etched": T("wall-etched"), "bh-kick": T("bh-kick"), "brushedv": T("brushedv"),
                         "ledgreen": T("ledgreen"), "bezel": T("bezel"), "bh-head": T("bh-head")})
    for i in range(len(LINE_COLOURS)):
        els = panel_els() + [
            box("Post", (1, 0, -3), (15, 16, 0), "wall-beam"),
            box("StepW", (0, 0, -2), (1, 16, 0), "brushedv"),
            box("StepE", (15, 0, -2), (16, 16, 0), "brushedv"),
            uvfull(box("Plate", (3, 4, -3.25), (13, 13, -3), f"bh-code{i}", faces=("north",)), "north"),
        ]
        add(f"jambplate{i}", els, {"wall-beam": T("wall-beam"), "brushedv": T("brushedv"), f"bh-code{i}": T(f"bh-code{i}")})

    # The battery emergency lamp (twin heads on a box, the box's charge LED), lit amber (it gives a little light) or dead
    for lit in (True, False):
        lens = "emerglit" if lit else "emergdead"
        els = panel_els() + [
            box("Box", (3, 3, -2.5), (13, 8, 0), {"all": "whitegloss", "north": "whitegloss"}),
            box("Grille", (5, 3.5, -2.55), (11, 5, -2.5), "dark", faces=("north",)),
            box("Led", (11.5, 4, -2.6), (12.25, 4.75, -2.5), "ledgreen" if lit else "dark", faces=("north",), glow=200 if lit else 0),
            box("HeadW", (2.5, 8, -4), (7, 11.5, -0.5), {"all": "whitegloss", "north": lens}, rot=(-20, 0, 0), origin=(4.75, 8, -2)),
            box("HeadE", (9, 8, -4), (13.5, 11.5, -0.5), {"all": "whitegloss", "north": lens}, rot=(-20, 0, 0), origin=(11.25, 8, -2)),
        ]
        if lit:
            for e in els[-2:]:
                e["faces"]["north"]["glow"] = 230
        add("emerg" + ("lit" if lit else "dead"), els, {"whitegloss": T("whitegloss"), "dark": T("dark"), "ledgreen": T("ledgreen"),
                                                        lens: T(lens)}, light=[6, 5, 11] if lit else None)
    # The breaker panel by the dark: its door swung open, the breakers inside, one tripped, a tag on the door
    els = panel_els() + [
        box("Box", (3, 1, -1.5), (13, 14, 0), {"all": "steelgrey", "north": "breakers"}),
        box("Door", (13, 1, -1.5), (13.5, 14, 8.5), {"all": "steelgrey", "east": "lockerdoor"}, rot=(0, -60, 0), origin=(13.25, 7, -1.5)),
        box("Tag", (13.6, 5, 0), (13.7, 8, 3), "tag", faces=("east", "west"), rot=(0, -60, 0), origin=(13.25, 7, -1.5)),
        box("Conduit", (7, 14, -1), (9, 16, 0), "dark"),
    ]
    els[1]["faces"]["north"]["uv"] = [0, 0, 16, 16]
    add("breaker", els, {"steelgrey": T("steelgrey"), "breakers": T("breakers"), "lockerdoor": T("lockerdoor"), "dark": T("dark"), "tag": T("tag")})
    return out


def panel_textures():
    # A green cross lamp (lit, dead)
    for name, (bg, c) in (("medcross", ((226, 240, 232), (40, 200, 90))), ("medcrossdead", ((150, 156, 152), (60, 90, 70)))):
        img = M.new((S, S), bg)
        rect(img, 12, 4, 19, 27, c)
        rect(img, 4, 12, 27, 19, c)
        save(img, name)
    # The halls' tags (64 x 64, the plate's 10 x 7 face drawn in its middle rows): HALL and the name, an arrow each way
    from gen_15_r3 import HALLS
    for n, code in enumerate(HALLS):
        img = Image.new("RGBA", (B, B), (24, 28, 32, 255))
        rect(img, 1, 1, B - 2, B - 2, (34, 40, 46))
        rect(img, 1, 1, B - 2, 3, (200, 206, 210))
        draw_text(img, (4, 8, 26, 24), "HALL", (170, 180, 188), 7, condensed=True)
        draw_text(img, (28, 6, 60, 40), code, (236, 242, 246), 20)
        d = ImageDraw.Draw(img)
        d.polygon([(6, 50), (14, 44), (14, 56)], fill=(200, 206, 210, 255))
        d.polygon([(58, 50), (50, 44), (50, 56)], fill=(200, 206, 210, 255))
        rect(img, 14, 49, 50, 51, (200, 206, 210))
        save(img, f"tag{n}")
    # The ESCAPE button's parts, a hand-written tag
    save(M.painted_metal(seed=15840, base=(232, 190, 30), panel=False, chips=1), "yellowcollar")
    save(M.painted_metal(seed=15841, base=(170, 28, 24), panel=False, chips=0), "redbutton")
    img = Image.new("RGBA", (B, B), (230, 220, 180, 255))
    draw_text(img, (4, 8, B - 4, 30), "DO NOT", (60, 50, 140), 9, condensed=True)
    draw_text(img, (4, 32, B - 4, 54), "RESET", (60, 50, 140), 9, condensed=True)
    save(img, "tag")


def bulkhead_shape(axis, lit):
    """A bulkhead's header across a main hall (in the top block of air, under the ceiling): a deep white steel beam with
    a hazard strip along its foot both ways, a light bar under it, stiffeners. Modelled across x (we)."""
    light = "bh-light" if lit else "bh-lightdead"
    els = [box("Beam", (0, 2, 2), (16, 16, 14), {"all": "bh-head", "up": "wall-beam", "down": "wall-beam"}),
           box("FlangeN", (0, 2, 1.25), (16, 3, 2), "brushed"),
           box("FlangeS", (0, 2, 14), (16, 3, 14.75), "brushed"),
           box("LightHousing", (1, 1.25, 5.5), (15, 2, 10.5), "brushed"),
           box("Light", (1.5, 1.15, 6), (14.5, 1.25, 10), light, faces=("down",), glow=220 if lit else 0),
           box("StiffN", (7.5, 3, 1.25), (8.5, 16, 2), "brushed"),
           box("StiffS", (7.5, 3, 14), (8.5, 16, 14.75), "brushed")]
    if axis == "ns":
        from modelkit import turn
        els = turn(els, 1)
    return write_shape(f"l15-bulkhead-{axis}-{'lit' if lit else 'dead'}", els,
                       {k: T(k) for k in ("bh-head", "wall-beam", "brushed", light)})


def glazing_shape(kind, row):
    """Thick glass in a steel frame (round 4), the pane across x (faces north and south), 8 thick: a sill (row lower)
    or a head rail (upper) standing off both faces, a mullion at the block's west edge, glazing beads round the pane.
    The pane only shows its two big faces (runs of glass meet without inner faces)."""
    g = "glass-" + kind
    els = [box("Pane", (0, 0, 4), (16, 16, 12), g, faces=("north", "south"))]
    if row == "lower":
        els += [box("Sill", (0, 0, 2.5), (16, 1.5, 13.5), {"all": "brushed", "up": "brushed"}),
                box("SillLipN", (0, 1.5, 3.5), (16, 2, 4), "bezel"), box("SillLipS", (0, 1.5, 12), (16, 2, 12.5), "bezel")]
    else:
        els += [box("Head", (0, 14.5, 2.5), (16, 16, 13.5), "brushed"),
                box("HeadLipN", (0, 14, 3.5), (16, 14.5, 4), "bezel"), box("HeadLipS", (0, 14, 12), (16, 14.5, 12.5), "bezel")]
    els += [box("Mullion", (0, 0, 2.75), (1.25, 16, 13.25), "brushedv"),
            box("BeadN", (1.25, 0, 3.6), (1.75, 16, 4), "bezel"), box("BeadS", (1.25, 0, 12), (1.75, 16, 12.4), "bezel")]
    for e in els[:1]:
        for f in e["faces"].values():
            f["uv"] = [0, 0, 16, 16]
    return els


def medmonitor_shape(lit):
    """A vitals monitor on a wall arm over a medical bed's head (the wall to the south): the headwall rail with its
    outlets, a wall plate, two arm links with a joint, a yoke and the monitor tilted down a little, its screen lit or
    dead, a handle on top, a cable. Of l14-monitor's family, white and clean for 15."""
    sc = "medscreen-lit" if lit else "medscreen-dead"
    tilt = dict(rot=(8, 0, 0), origin=(8, 10, 8))
    els = [box("Rail", (0, -4, 14.5), (16, 0.5, 16), {"all": "whitegloss", "north": "headwall"}),
           box("WallPlate", (6.5, 2, 15.25), (9.5, 8, 16), "brushed"),
           box("Arm1", (7.25, 4.25, 11), (8.75, 5.5, 15.25), "steelgrey"),
           box("Joint", (7, 4, 9.75), (9, 6, 11.25), "bezel"),
           box("Arm2", (7.4, 5.5, 9.9), (8.6, 7, 10.9), "steelgrey"),
           box("Yoke", (6.5, 7, 9), (9.5, 8, 10.5), "bezel"),
           box("Housing", (3, 6.5, 6.75), (13, 13.5, 9), "whitegloss", **tilt),
           box("Bezel", (3.4, 6.9, 6.6), (12.6, 13.1, 6.75), "bezel", faces=("north",), **tilt),
           uvfull(box("Screen", (3.9, 7.9, 6.5), (12.1, 12.6, 6.6), sc, faces=("north",), glow=170 if lit else 0, **tilt), "north"),
           box("Knob", (11.2, 7.1, 6.3), (12.2, 7.7, 6.6), "dark", **tilt),
           box("Handle", (5, 13.5, 7.25), (11, 14.25, 8.25), "steelgrey", **tilt),
           box("Cable", (8.25, -4, 15), (8.75, 2, 15.5), "dark")]
    els[-4]["faces"]["north"]["uv"] = [0, 0, 16, 16]
    return write_shape(f"l15-medmonitor-{'lit' if lit else 'dead'}", els,
                       {k: T(k) for k in ("whitegloss", "headwall", "brushed", "steelgrey", "bezel", "dark", sc)})


def lectern_shape(lit):
    """A lectern on the lecture hall's half-block stage (its base 8 below the block), its audience side to the north: a
    plinth, a white body with the hall line's stripe and a steel kick, a desk sloping toward the speaker, a gooseneck
    microphone and a reading lamp (lit, or dead in the dark)."""
    slope = dict(rot=(14, 0, 0), origin=(8, 6, 8))
    els = [box("Plinth", (3, -8, 4), (13, -7, 12.5), "bezel"),
           box("Body", (4, -7, 5), (12, 5.5, 11.5), {"all": "whitegloss", "north": "lecternfront"}),
           box("Kick", (4.25, -7, 4.75), (11.75, -6, 5), "brushed", faces=("north",)),
           box("Desk", (3.25, 5.5, 3.5), (12.75, 6.5, 12.5), {"all": "whitegloss", "top": "epoxy"}, **slope),
           box("Ledge", (3.25, 6.5, 12), (12.75, 7.25, 12.5), "brushed", **slope),
           box("MicBase", (5, 6.25, 5), (6, 6.75, 6), "bezel"),
           box("MicNeck", (5.3, 6.75, 5.3), (5.7, 11, 5.7), "bezel", rot=(20, 0, 0), origin=(5.5, 6.75, 5.5)),
           box("MicHead", (5.1, 10.4, 6.5), (5.9, 11.4, 7.6), "bezel"),
           box("LampNeck", (10.3, 6.5, 6.3), (10.7, 10.5, 6.7), "brushed", rot=(25, 0, 0), origin=(10.5, 6.5, 6.5)),
           box("LampHead", (9.5, 10, 7.5), (11.5, 11, 10), "brushed"),
           box("LampLens", (9.75, 9.9, 7.75), (11.25, 10, 9.75), "ledamber" if lit else "dark", faces=("down",), glow=200 if lit else 0)]
    els[1]["faces"]["north"]["uv"] = [0, 0, 16, 16]
    return write_shape(f"l15-lectern-{'lit' if lit else 'dead'}", els,
                       {k: T(k) for k in ("bezel", "whitegloss", "lecternfront", "brushed", "epoxy", "ledamber", "dark")})


def tray_shape():
    """A ladder cable tray along x near the top of a side corridor (round 4): two side rails, rungs, three bundles of
    cables in their colours with ties, carried on two trapezes (a strut channel under it on threaded rods to the
    ceiling)."""
    els = [box("RailN", (0, 10, 4), (16, 12, 4.5), "brushed"),
           box("RailS", (0, 10, 11.5), (16, 12, 12), "brushed")]
    for x in (1, 5, 9, 13):
        els.append(box(f"Rung{x}", (x, 10, 4.5), (x + 1, 10.4, 11.5), "brushed"))
    for i, (z0, z1, h, tx) in enumerate(((5, 7, 1.6, "cables"), (7.25, 9, 1.3, "cablesb"), (9.25, 11.25, 1.8, "cables"))):
        els.append(box(f"Bundle{i}", (0, 10.4, z0), (16, 10.4 + h, z1), tx))
        for x in (3.5, 11.5):
            els.append(box(f"Tie{i}{x}", (x, 10.35, z0 - 0.1), (x + 0.4, 10.5 + h, z1 + 0.1), "dark"))
    for x in (2.5, 12.5):
        els += [box(f"Strut{x}", (x, 9.25, 3), (x + 1, 10, 13), "steelgrey"),
                box(f"RodN{x}", (x + 0.35, 10, 3.35), (x + 0.65, 16, 3.65), "brushed"),
                box(f"RodS{x}", (x + 0.35, 10, 12.35), (x + 0.65, 16, 12.65), "brushed"),
                box(f"NutN{x}", (x + 0.2, 9.0, 3.2), (x + 0.8, 9.25, 3.8), "dark"),
                box(f"NutS{x}", (x + 0.2, 9.0, 12.2), (x + 0.8, 9.25, 12.8), "dark")]
    return write_shape("l15-tray", els, {k: T(k) for k in ("brushed", "cables", "cablesb", "dark", "steelgrey")})


MACHINE_KINDS = ["panel", "vent", "screen", "screenlit", "lights", "lightslit", "hatch", "warning", "furnace", "press", "burnt", "burntvent"]


def machine_shape(kind):
    """A machine's casing block (round 4): the cube with its face on all four sides as before, and on each side the
    relief of what the face shows: steel corner posts at the four edges (so a stack reads as one cabinet), louvres
    standing out of a vent, a bezel round a screen and its buttons, a frame round a lamp bank, a hatch's handle and
    hinges, a frame round an incinerator's mouth. Modelled on the north side and turned to the other three."""
    burnt = kind.startswith("burnt")
    face = "machine-" + kind
    top = "machine-burnttop" if burnt else "machine-top"
    trim = "machine-burnt" if burnt else "steelgrey"
    els = [box("Body", (0, 0, 0), (16, 16, 16), {"all": face, "up": top, "down": top})]
    side = [box("Post", (-0.35, 0, -0.35), (1, 16, 1), trim)]
    if kind in ("vent", "burntvent"):
        for k, y in enumerate((13.5, 12, 10.5, 9, 7.5, 6, 4.5, 3)):
            side.append(box(f"Louvre{k}", (2, y - 0.6, -0.8), (14, y, 0), trim, rot=(35, 0, 0), origin=(8, y, 0)))
    elif kind in ("screen", "screenlit"):
        side += [box("BezelT", (1.25, 13.5, -0.6), (14.75, 14.25, 0), "bezel"), box("BezelB", (1.25, 4.25, -0.6), (14.75, 5, 0), "bezel"),
                 box("BezelW", (14, 5, -0.6), (14.75, 13.5, 0), "bezel"), box("BezelE", (1.25, 5, -0.6), (2, 13.5, 0), "bezel")]
        for k, px in enumerate(range(6, 26, 4)):
            side.append(box(f"Btn{k}", (16 - (px + 3) / 2 + 0.1, 2.6, -0.45), (16 - px / 2 - 0.1, 3.4, 0), "bezel"))
    elif kind in ("lights", "lightslit"):
        side += [box("FrameT", (1.5, 13.75, -0.5), (14.5, 14.25, 0), "bezel"), box("FrameB", (1.5, 1.75, -0.5), (14.5, 2.25, 0), "bezel"),
                 box("FrameW", (14, 2.25, -0.5), (14.5, 13.75, 0), "bezel"), box("FrameE", (1.5, 2.25, -0.5), (2, 13.75, 0), "bezel")]
    elif kind == "hatch":
        side += [box("Handle", (4, 6.5, -0.9), (5.25, 9.5, -0.2), "brushed"), box("HandleBase", (3.75, 6, -0.25), (5.5, 10, 0), "steelgrey"),
                 box("Hinge0", (12.6, 3, -0.6), (13.4, 5, 0), "brushed"), box("Hinge1", (12.6, 10.5, -0.6), (13.4, 12.5, 0), "brushed")]
    elif kind == "furnace":
        side += [box("MouthT", (2, 12, -0.8), (14, 12.75, 0), "machine-burnt"), box("MouthB", (2, 2.25, -0.8), (14, 3, 0), "machine-burnt"),
                 box("MouthW", (13.25, 3, -0.8), (14, 12, 0), "machine-burnt"), box("MouthE", (2, 3, -0.8), (2.75, 12, 0), "machine-burnt")]
    from modelkit import turn
    for t in range(4):
        for e in turn(side, t):
            e["name"] = f"{e['name']}{t}"
            els.append(e)
    return write_shape("l15-machine-" + kind, els, {k: T(k) for k in
                       (face, top, trim, "bezel", "brushed", "steelgrey", "machine-burnt")})


def stardoor_shape(part):
    """The star door (round 4): a free-standing steel doorframe two blocks high, facing north and south, its posts with
    flanges and bolt heads, base plates bolted to the floor, a threshold plate, a lintel with a stiffener; in it the night
    sky with the blue star, a faint halo round the star standing in the opening."""
    lower = part == "lower"
    els = []
    for side, x0 in (("L", 0.5), ("R", 13.5)):
        els += [box(f"Post{side}", (x0, 0, 6.5), (x0 + 2, 16, 9.5), "steel"),
                box(f"FlangeN{side}", (x0 - 0.25, 0, 6.25), (x0 + 2.25, 16, 6.5), "steel"),
                box(f"FlangeS{side}", (x0 - 0.25, 0, 9.5), (x0 + 2.25, 16, 9.75), "steel")]
        for y in ((2, 8, 14) if lower else (2, 8)):
            els += [box(f"BoltN{side}{y}", (x0 + 0.75, y, 6.05), (x0 + 1.25, y + 0.5, 6.25), "dark", faces=("north",)),
                    box(f"BoltS{side}{y}", (x0 + 0.75, y, 9.75), (x0 + 1.25, y + 0.5, 9.95), "dark", faces=("south",))]
        if lower:
            els.append(box(f"Base{side}", (x0 - 0.75, 0, 5), (x0 + 2.75, 0.5, 11), "steel"))
    els.append(box("Sky", (2.5, 0, 7.75), (13.5, 16 if lower else 12, 8.25), "starfield", faces=("north", "south"), glow=120))
    if lower:
        els += [box("Sill", (2.5, 0, 6.5), (13.5, 0.5, 9.5), "steel", faces=("up", "north", "south")),
                box("SillStrip", (2.5, 0.5, 7.5), (13.5, 0.6, 8.5), "dark", faces=("up",))]
    else:
        els += [box("Lintel", (0.25, 12, 6.25), (15.75, 15, 9.75), "steel"),
                box("Stiffener", (7.5, 15, 7), (8.5, 16, 9), "steel"),
                box("Star", (7.5, 2.5, 7.25), (8.5, 3.5, 8.75), "starglow", glow=255),
                box("HaloN", (6.25, 1.25, 7.5), (9.75, 4.75, 7.6), "starhalo", faces=("north", "south"), glow=200),
                box("HaloS", (6.25, 1.25, 8.4), (9.75, 4.75, 8.5), "starhalo", faces=("north", "south"), glow=200)]
    for e in els:
        if e["name"] in ("Sky", "HaloN", "HaloS"):
            for f in e["faces"].values():
                f["uv"] = [0, 0, 16, 16] if e["name"] != "Sky" else f["uv"]
    return write_shape("l15-stardoor-" + part, els, {k: T(k) for k in ("steel", "dark", "starfield", "starglow", "starhalo")})


def corpse_shape(pose, with_spear):
    """The dead in lab coats (round 4: round 1's bodies with the coat's collar, pockets and buttons, a lanyard and an ID
    card, hair, both hands, the shoes' soles; the spear's binding wound round it). Sitting: back to the wall (south),
    legs out to the north. Lying across two blocks: head (head and trunk) and feet (legs)."""
    if pose == "sitting":
        lean = dict(rot=(-10, 0, 0), origin=(8, 2, 14))
        els = [
            box("Trunk", (4, 2, 10), (12, 11, 14), "labcoat", **lean),
            box("CollarL", (4.5, 9.5, 9.6), (7.5, 11.25, 10.4), "labcoat", rot=(-10, 0, 20), origin=(6, 10, 10)),
            box("CollarR", (8.5, 9.5, 9.6), (11.5, 11.25, 10.4), "labcoat", rot=(-10, 0, -20), origin=(10, 10, 10)),
            box("Shirt", (6.75, 6, 9.85), (9.25, 10.5, 10), "trousers", faces=("north",), **lean),
            box("Pocket", (9, 4, 9.8), (11.25, 6.25, 10), "labcoatdark", faces=("north",), **lean),
            box("Lanyard", (7.75, 6.5, 9.7), (8.25, 10.5, 9.85), "ledred", faces=("north",), **lean),
            uvfull(box("Card", (7, 4.75, 9.6), (9, 6.75, 9.75), "idcard", faces=("north",), **lean), "north"),
            box("Head", (5.5, 11, 9.5), (10.5, 15, 13.5), "skin", rot=(-20, 0, 0), origin=(8, 11, 12)),
            box("Hair", (5.25, 13.5, 10.5), (10.75, 15.4, 13.8), "hair", rot=(-20, 0, 0), origin=(8, 11, 12)),
            box("CoatSkirt", (3.5, 0, 6), (12.5, 3, 14), "labcoat"),
            box("LegL", (4.5, 0, 0.5), (7.5, 2.5, 7), "trousers"),
            box("LegR", (8.5, 0, 1.5), (11.5, 2.5, 7), "trousers"),
            box("ShoeL", (4.25, 0, -0.5), (7.75, 3, 1.5), "shoe"),
            box("ShoeR", (8.25, 0, 0.5), (11.75, 3, 2.5), "shoe"),
            box("ArmL", (2.5, 1, 7), (4.5, 8, 11), "labcoat"),
            box("HandL", (2.6, 0, 6), (4.4, 1.25, 8), "bone"),
            box("ArmR", (11.5, 0, 4), (13.5, 2, 11), "labcoat"),
            box("HandR", (11.5, 0, 2.5), (13.5, 1.5, 4), "bone"),
        ]
    elif pose == "head":
        els = [
            box("Head", (5.5, 0, 11), (10.5, 4.5, 15.5), "skin"),
            box("Hair", (5.25, 0, 13.5), (10.75, 4.75, 15.9), "hair"),
            box("Jaw", (6.5, 0, 10.2), (9.5, 1.5, 11), "bone"),
            box("Trunk", (3.5, 0, 0), (12.5, 4, 10.5), "labcoat"),
            box("Shirt", (6.75, 4, 6), (9.25, 4.1, 10.5), "trousers", faces=("up",)),
            box("CollarL", (4.5, 4, 8.5), (7, 4.4, 10.5), "labcoat"),
            box("CollarR", (9, 4, 8.5), (11.5, 4.4, 10.5), "labcoat"),
            box("Pocket", (9, 4, 2), (11.5, 4.1, 4.5), "labcoatdark", faces=("up",)),
            box("Lanyard", (7.75, 4.05, 4), (8.25, 4.15, 9), "ledred", faces=("up",)),
            uvfull(box("Card", (6.5, 4, 1.5), (9, 4.3, 4), {"all": "white", "up": "idcard"}, rot=(0, 25, 0), origin=(7.75, 4, 2.75)), "up"),
            box("ArmL", (1.5, 0, 1), (3.5, 2.5, 10), "labcoat"),
            box("HandL", (1.6, 0, -0.5), (3.4, 1.25, 1), "bone"),
            box("ArmR", (12.5, 0, 0), (14.5, 2.5, 7), "labcoat"),
            box("HandR", (12.5, 0, -1.5), (14.5, 1.5, 0), "bone"),
        ]
    else:
        els = [
            box("CoatSkirt", (3.5, 0, 9), (12.5, 3, 16), "labcoat"),
            box("CoatHem", (3.25, 0, 8.5), (12.75, 2.25, 9), "labcoatdark"),
            box("LegL", (4, 0, 2), (7.5, 2.5, 13), "trousers"),
            box("LegR", (8.5, 0, 1), (12, 2.5, 12), "trousers"),
            box("ShoeL", (3.75, 0, 0), (7.75, 3.5, 2), "shoe"),
            box("ShoeR", (8.25, 0, -0.5), (12.25, 3.5, 1.5), "shoe"),
            box("SoleL", (3.75, 0, -0.1), (7.75, 0.75, 0), "dark", faces=("north",)),
            box("SoleR", (8.25, 0, -0.6), (12.25, 0.75, -0.5), "dark", faces=("north",)),
        ]
    if with_spear:
        els += [box("Shaft", (0, 0, 13), (13, 0.75, 13.75), "pipe"),
                box("Tape", (11.5, 0, 12.85), (14, 0.9, 13.9), "tape"),
                box("Wrap0", (12, 0, 12.75), (12.4, 1, 14), "tape"),
                box("Wrap1", (13.2, 0, 12.75), (13.6, 1, 14), "tape"),
                box("Blade", (13.5, 0, 13), (16, 0.5, 13.75), "shard"),
                box("BladeTip", (15.5, 0, 13.15), (16.75, 0.35, 13.6), "shard")]
    return write_shape(f"l15-corpse-{pose}-{'spear' if with_spear else 'plain'}", els, {k: T(k) for k in
                       ("labcoat", "labcoatdark", "trousers", "ledred", "idcard", "skin", "hair", "bone", "shoe", "white", "dark",
                        "pipe", "tape", "shard")})


def stool_shape():
    """A canteen's fixed stool: a floor flange, a steel column, a foot ring, a round seat (two crossed boxes and a cap)."""
    els = [box("Flange", (5.5, 0, 5.5), (10.5, 0.4, 10.5), "brushed"),
           box("Column", (7.25, 0.4, 7.25), (8.75, 7, 8.75), "brushed")]
    for k in range(8):
        els.append(box(f"Ring{k}", (6.55, 2.5, 11.25), (9.45, 3, 11.75), "brushed", rot=(0, k * 45, 0), origin=(8, 2.75, 8)))
    for k in range(4):
        els.append(box(f"Spoke{k}", (7.75, 2.55, 8.5), (8.25, 2.95, 11.25), "brushed", rot=(0, k * 90 + 45, 0), origin=(8, 2.75, 8)))
    els += [box("SeatA", (4.5, 7, 3.5), (11.5, 8.5, 12.5), "seatcloth"),
            box("SeatB", (3.5, 7, 4.5), (12.5, 8.5, 11.5), "seatcloth"),
            box("Rim", (4, 6.75, 4), (12, 7.1, 12), "bezel")]
    return write_shape("l15-stool", els, {k: T(k) for k in ("brushed", "seatcloth", "bezel")})


def ctable_shape():
    """A canteen table block: a white laminate top on an aluminium edge, a T pedestal under it (each block its own, so
    a run reads as one long table on a row of pedestals)."""
    els = [box("Top", (0, 12, 0), (16, 13, 16), {"all": "brushed", "top": "laminate", "bottom": "steelgrey"}),
           box("Apron", (0.5, 11, 3), (15.5, 12, 13), "steelgrey"),
           box("Column", (7, 1, 7), (9, 11, 9), "brushed"),
           box("FootX", (2, 0, 7), (14, 1, 9), "bezel"),
           box("FootZ", (7, 0, 2), (9, 1, 14), "bezel"),
           box("Cap", (6, 10.5, 6), (10, 11, 10), "steelgrey")]
    return write_shape("l15-ctable", els, {k: T(k) for k in ("brushed", "laminate", "steelgrey", "bezel")})


def labbench_shape(kind):
    """A lab bench (round 4), its front to the north: a white carcase on a recessed kick, two cabinet doors with bar
    pulls, a black epoxy top; at the back a service spine (a gas tap with its yellow handle, a socket box) and a reagent
    shelf on two posts; on top a sink with a gooseneck tap and wrist handles, a microscope and an analyser, or glassware
    (flasks, beakers, a rack of test tubes, bottles on the shelf). The glass is opaque (no translucent texels here)."""
    els = [box("Kick", (1, 0, 2.5), (15, 1.5, 15), "dark"),
           box("Carcase", (0.5, 1.5, 2), (15.5, 13, 15.5), "white"),
           box("DoorW", (8.25, 2, 1.5), (15, 12.5, 2), "whitegloss"),
           box("DoorE", (1, 2, 1.5), (7.75, 12.5, 2), "whitegloss"),
           box("PullW", (8.75, 8.5, 1.0), (9.25, 11.5, 1.5), "brushed"),
           box("PullE", (6.75, 8.5, 1.0), (7.25, 11.5, 1.5), "brushed"),
           box("Top", (0, 13, 0.5), (16, 14.5, 16), "epoxy"),
           box("SpineW", (1, 14.5, 14), (1.75, 24, 15), "brushed"),
           box("SpineE", (14.25, 14.5, 14), (15, 24, 15), "brushed"),
           box("Shelf", (0.5, 21, 12.5), (15.5, 21.75, 15.5), "whitegloss"),
           box("GasTap", (3, 14.5, 13.5), (4, 16.25, 14.5), "brushed"),
           box("GasHandle", (2.5, 16, 12.5), (4.5, 16.5, 13.75), "yellowcollar"),
           box("Socket", (10, 14.5, 14.5), (13, 16.75, 15.5), {"all": "whitegloss", "north": "bezel"})]
    if kind == "sink":
        els += [box("Basin", (4, 14.4, 4), (12, 14.5, 11), "dark", faces=("up",)),
                box("RimN", (3.5, 14.5, 3.5), (12.5, 14.75, 4), "sinksteel"), box("RimS", (3.5, 14.5, 11), (12.5, 14.75, 11.5), "sinksteel"),
                box("RimW", (3.5, 14.5, 4), (4, 14.75, 11), "sinksteel"), box("RimE", (12, 14.5, 4), (12.5, 14.75, 11), "sinksteel"),
                box("Riser", (7.5, 14.5, 12.5), (8.5, 21, 13.5), "sinksteel"),
                box("Neck", (7.5, 20, 9), (8.5, 21, 13.5), "sinksteel"),
                box("Spout", (7.6, 18.5, 9), (8.4, 20, 9.8), "sinksteel"),
                box("WristW", (8.5, 16.5, 12.75), (11, 17, 13.25), "sinksteel"),
                box("WristE", (5, 16.5, 12.75), (7.5, 17, 13.25), "sinksteel")]
    elif kind == "equipment":
        tube = dict(rot=(25, 0, 0), origin=(5.5, 19, 9))
        els += [box("ScopeBase", (3, 14.5, 7), (8, 15.25, 12), "whitegloss"),
                box("ScopeArm", (4.75, 15.25, 10.5), (6.25, 21, 12), "whitegloss"),
                box("ScopeStage", (3.5, 17, 6.5), (7.5, 17.5, 10), "bezel"),
                box("ScopeHead", (4.5, 20, 8), (6.5, 22, 11.5), "whitegloss"),
                box("ScopeTube", (4.9, 18, 7.2), (6.1, 23.5, 8.4), "bezel", **tube),
                box("Analyser", (9, 14.5, 5), (14.5, 19.5, 12), {"all": "white", "north": "machine-lights", "top": "steelgrey"}),
                box("AnalyserLid", (9.5, 19.5, 6), (14, 20, 11.5), "steelgrey")]
    elif kind == "glassware":
        for i, (x, z, h) in enumerate(((3, 5, 4), (12, 9.5, 5))):
            els += [box(f"Flask{i}", (x, 14.5, z), (x + 2.6, 16, z + 2.6), "flask"),
                    box(f"FlaskMid{i}", (x + 0.5, 16, z + 0.5), (x + 2.1, 16.8, z + 2.1), "flask"),
                    box(f"FlaskNeck{i}", (x + 0.9, 16.8, z + 0.9), (x + 1.7, 14.5 + h, z + 1.7), "flask")]
        for i, (x, z) in enumerate(((6.5, 8), (9, 4.5))):
            els += [box(f"Beaker{i}", (x, 14.5, z), (x + 2, 17, z + 2), "flask"),
                    box(f"Liquid{i}", (x - 0.01, 14.6, z - 0.01), (x + 2.01, 15.6, z + 2.01), "liquid" if i else "flask")]
        els += [box("Rack", (3, 14.5, 9.5), (8, 15.5, 11.5), "steelgrey"), box("RackTop", (3, 16.5, 9.5), (8, 17, 11.5), "steelgrey")]
        for k in range(4):
            els.append(box(f"Tube{k}", (3.6 + k * 1.15, 15.5, 10.1), (4.2 + k * 1.15, 18.5, 10.9), "flask"))
        els += [box("Bottle0", (2, 21.75, 13), (3.5, 24, 14.5), "amberglass"), box("Bottle1", (5, 21.75, 13), (6.5, 23.5, 14.5), "flask"),
                box("Bottle2", (11, 21.75, 13), (12.5, 24.25, 14.5), "amberglass")]
    return write_shape("l15-labbench-" + kind, els, {k: T(k) for k in
                       ("dark", "white", "whitegloss", "brushed", "epoxy", "yellowcollar", "bezel", "sinksteel", "machine-lights",
                        "steelgrey", "flask", "liquid", "amberglass")})


def locker_shape(part, state):
    """Two steel lockers side by side (round 4), two blocks high, their doors to the north: each door in its frame,
    louvres, a lift handle and a number plate; ajar: the left door swung open on its hinges, inside a shelf and a rail
    (upper) and a lab coat left hanging (lower); the carcase on a plinth, a sloped top."""
    lower = part == "lower"
    top = 16 if lower else 14.5
    if state == "ajar":
        # The left locker hollow (its back, its outer side, its floor), the right one solid
        els = [box("Carcase", (8.25, 0, 2), (15.5, top, 15.5), "steelgrey"),
               box("BackL", (0.5, 0, 14.5), (8.25, top, 15.5), "steelgrey"),
               box("SideL", (0.5, 0, 2), (1, top, 14.5), "steelgrey"),
               box("FloorL", (1, 0, 2), (8.25, 1, 14.5), "steelgrey") if lower else box("CeilL", (1, top - 0.5, 2), (8.25, top, 14.5), "steelgrey")]
    else:
        els = [box("Carcase", (0.5, 0, 2), (15.5, top, 15.5), "steelgrey")]
    if lower:
        els.append(box("Plinth", (0.5, 0, 1.4), (15.5, 1, 2), "dark", faces=("north", "east", "west")))
    else:
        els += [box("Top", (0.25, 14.5, 1.5), (15.75, 15.25, 15.75), "steelgrey"),
                box("Slope", (0.5, 14.5, 4), (15.5, 15.5, 15.5), "steelgrey", rot=(-12, 0, 0), origin=(8, 15.25, 15.5))]
    els.append(box("Stile", (7.5, 1 if lower else 0, 1.5), (8.5, 16 if lower else 14.5, 2), "steelgrey"))
    y0, y1 = (1, 16) if lower else (0, 14.25)
    for i, x0 in enumerate((0.75, 8.5)):
        open_ = state == "ajar" and i == 0
        tex = {"all": "steelgrey", "north": "lockervents" if (not lower) else "lockerdoor"}
        door = [box(f"Door{i}", (x0, y0, 1.5), (x0 + 6.75, y1, 2), tex)]
        if lower:
            door += [box(f"Handle{i}", (x0 + 5.25, 12, 1.0), (x0 + 6, 15.5, 1.5), "brushed"),
                     box(f"Vents{i}", (x0 + 1, 2, 1.45), (x0 + 5.75, 4, 1.5), "lockervents", faces=("north",))]
        else:
            door += [uvfull(box(f"Number{i}", (x0 + 2.5, 11, 1.4), (x0 + 4.25, 12, 1.5), "brushed", faces=("north",)), "north")]
        if open_:
            for e in door:
                e["rotationOrigin"] = [x0, 8, 1.75]
                e["rotationY"] = 70
            els += [box("Inside", (1, 0, 14.4), (8.25, top, 14.5), "dark", faces=("north",))]
            if not lower:
                els += [box("Shelf", (x0, 8, 2.2), (x0 + 6.75, 8.5, 15), "steelgrey"),
                        box("Rail", (x0, 6, 8), (x0 + 6.75, 6.4, 8.4), "brushed")]
            else:
                els += [box("Coat", (x0 + 1.5, 3, 9), (x0 + 5.5, 16, 12.5), "labcoat"),
                        box("Hanger", (x0 + 1, 15.25, 10.5), (x0 + 6, 15.75, 11), "brushed")]
        els += door
    return write_shape(f"l15-locker-{part}-{state}", els, {k: T(k) for k in
                       ("steelgrey", "dark", "lockerdoor", "lockervents", "brushed", "labcoat")})


def glass_textures():
    """The bench glassware and the spears' blades as opaque glass looks (pale, a bright edge, a highlight): the labs'
    benches and the dead are in the opaque pass, where translucent texels take the sky's tint."""
    for name, base in (("flask", (196, 222, 226)), ("shard", (190, 214, 218))):
        img = M.new((S, S), base)
        for y in range(S):
            for x in range(S):
                if x in (0, 31) or y in (0, 31):
                    blend(img, x, y, (240, 252, 255), 0.6)
                if 4 <= x <= 6 and 3 <= y <= 26:
                    blend(img, x, y, (250, 255, 255), 0.55)
        M.grime(img, 0.05, seed=15850, color=(150, 160, 160))
        save(opaque(img), name)
    save(M.new((S, S), (140, 70, 20)), "amberglass")
    # The dead's ID card (a photo square, lines of print, a coloured band), the coat's shaded fold, hair
    img = Image.new("RGBA", (S, S), (236, 238, 236, 255))
    rect(img, 0, 0, S - 1, 6, LINE_COLOURS[0])
    rect(img, 3, 10, 13, 22, (150, 140, 130))
    for y in (11, 15, 19):
        rect(img, 16, y, 28, y + 1, (60, 64, 70))
    rect(img, 3, 26, 28, 28, (40, 44, 50))
    save(img, "idcard")
    coat = load("labcoat")
    a = np.array(coat).astype(float)
    a[..., :3] *= 0.8
    save(Image.fromarray(a.clip(0, 255).astype("uint8"), "RGBA"), "labcoatdark")
    save(M.noise_hv((58, 46, 36), amp=6, seed=15870, mottle=8), "hair")
    # The star door's sky without its star (the star stands in the opening as a model): a night sky, small stars
    sky = M.new((S, S), (4, 6, 14))
    rng = random.Random(15516)
    for _ in range(30):
        x, y = rng.randint(0, 31), rng.randint(0, 31)
        b = rng.randint(110, 240)
        sky.putpixel((x, y), (b, b, min(255, b + 20), 255))
    save(sky, "starfield")
    # The blue star's halo: a soft ring of blue (a cut-out: opaque where it shows, gone outside it)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for y in range(S):
        for x in range(S):
            d = ((x - 15.5) ** 2 + (y - 15.5) ** 2) ** 0.5
            if 9 <= d <= 15 and (x + y) % 2 == 0:
                k = 1 - abs(d - 12) / 3
                img.putpixel((x, y), (int(60 + 80 * k), int(110 + 100 * k), 255, 255))
    save(img, "starhalo")
    # A second bundle's colours (greys, an orange fibre, a green earth)
    img = M.new((S, S), (28, 30, 32))
    for y in range(S):
        c = [(70, 72, 76), (230, 120, 30), (28, 30, 32), (60, 140, 70), (90, 92, 96), (28, 30, 32), (220, 220, 210), (50, 52, 56)][y // 4]
        for x in range(S):
            img.putpixel((x, y), tuple(int(v * (0.8 + 0.2 * ((y % 4) in (1, 2)))) for v in c) + (255,))
    save(img, "cablesb")
    save(M.new((S, S), (120, 200, 160)), "liquid")


# ======================================================================== Block types

def blocktypes():
    from gen_15_r3 import HALLS

    # Rewritten in place: consoles, docks, seats, risers, serving line, racks, curtains (round 3's blocktypes reference
    # these shape files; their textures come with each shape)
    for st in ("dead", "denied", "radar"):
        console_shape(st)
    for k in ("plain", "sink", "equipment", "glassware"):
        labbench_shape(k)
    tray_shape()
    for pose in ("sitting", "head", "feet"):
        for spear in (False, True):
            corpse_shape(pose, spear)
    for part in ("lower", "upper"):
        stardoor_shape(part)
    for part in ("lower", "upper"):
        for st in ("closed", "ajar"):
            locker_shape(part, st)
    for part in ("lower", "upper"):
        for lit in (True, False):
            dock_shape(part, lit)
            growrack_shape(part, lit)
        curtain_shape(part)
    for k in ("lo", "hi"):
        seat_shape(k)
    for k in ("half", "full"):
        riser_shape(k)
    for k in ("wells", "trays", "till"):
        serve_shape(k)
    for axis in ("we", "ns"):
        for part in range(3):
            write_shape(f"l15-hangsign-{part}-{axis}", hangsign_shape(part, axis),
                        {"front": T("hang0-lit-0"), "back": T("hang0-lit-0"), "rim": T("dark"), "frame": T("brushed"), "edge": T("bh-light")})

    # The dock's and the serving line's blocktypes: the serving line needs nothing new; the dock's eye glow is in its shape

    # l15-panel
    shapes = panel_shapes()
    kinds = list(shapes)
    sbt, light = {}, {}
    for k, (base, lt) in shapes.items():
        for s in SIDES:
            sbt[f"*-{k}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
        if lt:
            light[f"*-{k}-*"] = lt
    data = {"code": "l15-panel", "variantgroups": [{"code": "kind", "states": kinds}, {"code": "side", "states": SIDES}],
            "shapeByType": sbt, "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]},
            "blockmaterial": "Stone", "drawtype": "json", "sidesolid": {"all": True}, "sideopaque": {"all": True},
            "lightAbsorption": 99, "lightAbsorptionByType": {"*-lampon-*": 0, "*-emerglit-*": 0, "*-medheadlit-*": 0, "*-radar-*": 0, "*-view*": 0, "*": 99},
            "resistance": 6, "drops": [], "sounds": STONE, "lightHsvByType": light,
            "emitSideAo": {"all": False}}
    write_json(os.path.join(BLOCKS, "l15-panel.json"), data,
               "Level 15 (round 4): a white wall block with a model on its face toward its side: the fire extinguisher, the ESCAPE "
               "panel, the lift (leaves in a portal, the lit indicator, the call panel), the big display's bezel, the bulkheads' "
               "jambs and code plates, the battery emergency lamp, the tripped breaker panel")

    # l15-bulkhead
    sbt = {}
    for axis in ("we", "ns"):
        for lit in (True, False):
            sbt[f"*-{'lit' if lit else 'dead'}-{axis}"] = {"base": bulkhead_shape(axis, lit)}
    json_block("l15-bulkhead", [{"code": "state", "states": ["lit", "dead"]}, {"code": "axis", "states": ["we", "ns"]}], sbt,
               "Level 15 (round 4): a bulkhead's deep header across a main hall, a light bar under it (lit, dead)",
               {"collisionbox": cuboid((0, 0.1, 0, 1, 1, 1)), "selectionbox": cuboid((0, 0.1, 0, 1, 1, 1))},
               inventory="l15-bulkhead-lit-we")

    # The serving line in the opaque pass now (its guard a cut-out): round 3's blocktype without its Transparent pass
    path = os.path.join(BLOCKS, "l15-serve.json")
    with open(path, encoding="utf-8") as fh:
        head, body = fh.read().split("\n", 1)
    d = json.loads(body)
    d.pop("renderpass", None)
    write_json(path, d, head[3:])

    # l15-glazing
    sbt = {}
    for kind in ("clear", "cracked"):
        for row in ("lower", "upper"):
            base = write_shape(f"l15-glazing-{kind}-{row}", glazing_shape(kind, row),
                               {k: T(k) for k in (f"glass-{kind}", "brushed", "brushedv", "bezel")})
            sbt[f"*-{kind}-{row}-we"] = {"base": base}
            sbt[f"*-{kind}-{row}-ns"] = {"base": base, "rotateY": 90}
    data = {"code": "l15-glazing", "variantgroups": [{"code": "kind", "states": ["clear", "cracked"]},
                                                     {"code": "row", "states": ["lower", "upper"]}, {"code": "axis", "states": ["we", "ns"]}],
            "shapeByType": sbt, "creativeinventory": {"general": ["*-lower-we"], "backrooms": ["*-lower-we"]},
            "blockmaterial": "Glass", "drawtype": "json", "renderpass": "Transparent", "sidesolid": {"all": False},
            "sideopaque": {"all": False}, "lightAbsorption": 1, "resistance": 4, "sounds": GLASS,
            "drops": [{"type": "item", "code": "glassshard", "quantity": {"avg": 2, "var": 1}}],  # as l15-glass
            "collisionboxByType": {"*-we": cuboid((0, 0, 0.15, 1, 1, 0.85)), "*": cuboid((0.15, 0, 0, 0.85, 1, 1))},
            "selectionboxByType": {"*-we": cuboid((0, 0, 0.15, 1, 1, 0.85)), "*": cuboid((0.15, 0, 0, 0.85, 1, 1))}}
    write_json(os.path.join(BLOCKS, "l15-glazing.json"), data,
               "Level 15 (round 4): the thick glass walls in a steel frame (clear, cracked; lower with its sill, upper with its head)")

    # l15-medmonitor
    shapes = {}
    for lit in (True, False):
        base = medmonitor_shape(lit)
        for s in SIDES:
            shapes[f"*-{'lit' if lit else 'dead'}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    json_block("l15-medmonitor", [{"code": "state", "states": ["lit", "dead"]}, {"code": "side", "states": SIDES}], shapes,
               "Level 15 (round 4): a vitals monitor on a wall arm over a medical bed's head, on the headwall rail (lit, dead), "
               "facing its side",
               {"collisionbox": cuboid((0, 0, 0, 0, 0, 0)), "selectionboxByType": {
                   "*-north": cuboid((0.15, 0.3, 0.4, 0.85, 0.9, 1)), "*-east": cuboid((0, 0.3, 0.15, 0.6, 0.9, 0.85)),
                   "*-south": cuboid((0.15, 0.3, 0, 0.85, 0.9, 0.6)), "*-west": cuboid((0.4, 0.3, 0.15, 1, 0.9, 0.85))}},
               extra={"lightHsvByType": {"*-lit-*": [10, 3, 4]},
                      "drops": [{"type": "item", "code": "scrapwire", "quantity": {"avg": 0.6, "var": 0.4}}]},
               inventory="l15-medmonitor-lit-north")

    # l15-lectern
    img = Image.new("RGBA", (B, B), (232, 234, 234, 255))
    rect(img, 6, 14, B - 7, 17, LINE_COLOURS[0])
    draw_text(img, (6, 22, B - 6, 34), "LEVEL 15", (60, 66, 74), 7, condensed=True)
    draw_text(img, (6, 36, B - 6, 44), "LECTURE HALL", (110, 116, 124), 4, condensed=True)
    M.grime(img, 0.05, seed=15860, color=(170, 170, 166), bias="bottom")
    save(img, "lecternfront")
    shapes = {}
    for lit in (True, False):
        base = lectern_shape(lit)
        for s in SIDES:
            shapes[f"*-{'lit' if lit else 'dead'}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    json_block("l15-lectern", [{"code": "state", "states": ["lit", "dead"]}, {"code": "side", "states": SIDES}], shapes,
               "Level 15 (round 4): a lectern on a lecture hall's stage, facing its side, its reading lamp lit or dead",
               {"collisionbox": cuboid((0.2, -0.5, 0.25, 0.8, 0.45, 0.8)), "selectionbox": cuboid((0.2, -0.5, 0.25, 0.8, 0.5, 0.8))},
               extra={"lightHsvByType": {"*-lit-*": [8, 3, 5]},
                      "drops": [{"type": "item", "code": "metalbracket", "quantity": {"avg": 0.3, "var": 0.3}}]},
               inventory="l15-lectern-lit-north")

    # l15-machine as models (round 4): the same block codes, textures, light, sounds and drops; the shapes add the relief
    path = os.path.join(BLOCKS, "l15-machine.json")
    with open(path, encoding="utf-8") as fh:
        head, body = fh.read().split("\n", 1)
    d = json.loads(body)
    d.pop("texturesByType", None)
    d["drawtype"] = "json"
    d["shapeByType"] = {f"*-{k}": {"base": machine_shape(k)} for k in MACHINE_KINDS}
    d["sidesolid"] = {"all": True}
    d["sideopaque"] = {"all": True}
    write_json(path, d, head[3:])

    # l15-stool, l15-ctable (one variant each)
    for code, shape_fn, coll, comment in (
            ("l15-stool", stool_shape, cuboid((0.22, 0, 0.22, 0.78, 0.53, 0.78)), "Level 15 (round 4): a canteen's fixed stool"),
            ("l15-ctable", ctable_shape, cuboid((0, 0, 0, 1, 0.8125, 1)),
             "Level 15 (round 4): a canteen table block (laminate on a pedestal); a run of them is one long table")):
        data = {"code": code, "shape": {"base": shape_fn()}, "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
                "blockmaterial": "Metal", "drawtype": "json", "sidesolid": {"all": False}, "sideopaque": {"all": False},
                "lightAbsorption": 0, "resistance": 3, "sounds": METAL, "collisionbox": coll, "selectionbox": coll,
                "drops": [{"type": "item", "code": "metalbracket", "quantity": {"avg": 0.3, "var": 0.3}}]}
        write_json(os.path.join(BLOCKS, code + ".json"), data, comment)

    # The hanging signs' blocktype, as round 3's with the frame and the lit edge (lit: bright; off: dark)
    shapes, tbt = {}, {}
    for axis in ("we", "ns"):
        for part in range(3):
            base = T(f"l15-hangsign-{part}-{axis}")
            for n in range(len(HALLS)):
                for st in ("lit", "off"):
                    key = f"*-{n}-{st}-{part}-{axis}"
                    shapes[key] = {"base": base}
                    tbt[key] = {"front": {"base": T(f"hang{n}-{st}-{part}")}, "back": {"base": T(f"hang{n}-{st}-{2 - part}")},
                                "rim": {"base": T("dark")}, "frame": {"base": T("brushed")},
                                "edge": {"base": T("bh-light" if st == "lit" else "bh-lightdead")}}
    hb = {"we": (0, 0.2, 0.43, 1, 0.92, 0.57), "ns": (0.43, 0.2, 0, 0.57, 0.92, 1)}
    json_block("l15-hangsign", [{"code": "hall", "states": [str(n) for n in range(len(HALLS))]}, {"code": "state", "states": ["lit", "off"]},
                                {"code": "part", "states": ["0", "1", "2"]}, {"code": "axis", "states": ["we", "ns"]}], shapes,
               "Level 15: a sign hung from the ceiling across a main hall before a crossing (three blocks, parts 0-2), the hall's name on "
               "both faces in a steel frame, its lower edge lit (off in the dark)",
               {"collisionbox": cuboid((0, 0, 0, 0, 0, 0)),
                "selectionboxByType": {"*-we": cuboid(hb["we"]), "*-ns": cuboid(hb["ns"])}},
               extra={"texturesByType": tbt, "vertexFlagsByType": {"*-lit-*": {"glowLevel": 200}},
                      "lightHsvByType": {"*-lit-1-*": [33, 3, 5]}},
               inventory="l15-hangsign-0-lit-1-we")


def main():
    textures()
    panel_textures()
    glass_textures()
    blocktypes()
    print("Level 15 round 4: textures, shapes and blocktypes written")


if __name__ == "__main__":
    main()
