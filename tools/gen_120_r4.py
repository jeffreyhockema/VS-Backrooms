"""Level 120, "Broken Servos": round 4's assets (the asset-quality pass, 2026-11-02). Rebuilds the level's main objects
as geometry rather than pictures on boxes, on matlib materials, and adds the round's new set pieces:

    l120-rack       a 2 m cabinet in two blocks (lower, upper) that read as one: carcass, a perforated front door (cut-out
                    mesh, servers and their LEDs seen through it), hinges and a swing handle, the servers recessed behind
                    it on their rails, a perforated rear door over cable looms and a PDU strip; kinds by state: servers
                    behind a door (off, leda, ledb, both), a storage array with drive shelves and no door (store,
                    storelit), a network rack with patch panels, switches and patch cords (net, netlit), gutted (its
                    door hanging off a hinge, the servers gone but one pulled half out, cables down its front)
    l120-wreck      a rack toppled onto its back, a rack torn open (two high), from the same parts
    l120-ups        a UPS cabinet, two high: plinth, louvred door, display and keypad, a breaker row behind a window, plates;
                    torn open: the door down, the battery trays and boards inside
    l120-battery    a battery cabinet, two high: frame, a door of bars, sealed batteries on shelves with their terminals
    l120-crac       a downflow cooling unit, two high, and its duct: panels with latches, louvres, a control panel with a
                    display, the duct with flanges and foil tape; open: its panel off, the fans and the coil
    l120-terminal   an operator's desk (drawer pedestal, modesty panel) with a CRT (bezel, recessed glass, tapered back), a
                    keyboard, a mouse and a binder: dead, smashed, or BOOT
    l120-console    (new) an operator's desk with two flat monitors on an arm clamped to its back edge: dead or one glitched
    l120-tray       a ladder rack: stringers and rungs on trapeze hangers, cable looms tied on it, a yellow fibre raceway
    l120-kvm        a KVM cart: a tubular frame on casters, a push handle, a monitor on a post, keyboard, a box below
    l120-floor      the raised floor: 2 x 2 panels a block with bevelled edges, perforated vents, grommets, grime
    l120-firesup    (new) the fire suppression bank, two high: red agent cylinders strapped to a rack, valve heads, the
                    manifold and the discharge pipe into the ceiling
    l120-tapelib    (new) a tape library cabinet, two high: a smashed window onto the tape slots and the robot's gantry

Every block faces north in its shape and is turned for its side. Run from gen_120.py's main (it runs after gen_120 and
gen_120_detail, overwriting the shapes and blocktypes of the blocks it rebuilds).
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

import matlib as M
from modelkit import box, PX, keypad, hinge
from gen_120 import (S, SIDES, ROTATE, BLOCKS, TEX, SHAPES, METAL, WOOD, STONE, write_json, json_block, drops, cuboid, FULL)

ALL = ("north", "east", "south", "west", "up", "down")
N_ = ("north",)
EXTERN = {
    # Shared textures of the mod (the released levels' EXIT sign and extinguisher), by key
    "x-exitface": "backrooms:block/detail/exitface", "x-exithousing": "backrooms:block/detail/exithousing",
}


def save(img, name):
    assert img.size[0] % 8 == 0 and img.size[1] % 8 == 0, (name, img.size)
    img = img.convert("RGBA")
    os.makedirs(TEX, exist_ok=True)
    img.save(os.path.join(TEX, name + ".png"))


def opaque(img):
    """Every texel fully opaque (the opaque pass tints translucent texels with the sky under fade)."""
    p = img.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = p[x, y]
            p[x, y] = (r, g, b, 255)
    return img


def cutout(img):
    """Alpha 0 or 255 only."""
    p = img.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = p[x, y]
            p[x, y] = (r, g, b, 255 if a >= 128 else 0)
    return img


def shape(name, els):
    keys = sorted({f["texture"][1:] for e in els for f in e["faces"].values()})
    tex = {k: EXTERN.get(k, "backrooms:block/120/" + k) for k in keys}
    write_json(os.path.join(SHAPES, name + ".json"), {"textureWidth": 16, "textureHeight": 16, "textures": tex, "elements": els})
    return "backrooms:block/120/" + name


def b(name, frm, to, tex, faces=ALL, **kw):
    return box(name, frm, to, tex, faces=faces, **kw)


def uvb(name, frm, to, tex, uv, faces=N_, glow=0, rest=None):
    """A box whose front face shows the texture rectangle `uv` (texture units, 16 a texture), its other faces `rest`."""
    el = box(name, frm, to, tex if rest is None else {"front": tex, "side": rest, "top": rest, "bottom": rest, "back": rest},
             faces=faces, glow=glow)
    if "north" in el["faces"]:
        el["faces"]["north"]["uv"] = list(uv)
    return el


def font(size):
    return ImageFont.load_default(size=size)


def hires(w, h, draw, bg=(0, 0, 0, 255), k=4):
    img = Image.new("RGBA", (w * k, h * k), bg)
    draw(img, ImageDraw.Draw(img), k)
    return opaque(img.resize((w, h), Image.LANCZOS))


def text_center(d, box_, text, size, fill):
    x0, y0, x1, y1 = box_
    f = font(size)
    l, t, r, bb = d.textbbox((0, 0), text, font=f)
    d.text(((x0 + x1 - (r - l)) / 2 - l, (y0 + y1 - (bb - t)) / 2 - t), text, font=f, fill=fill)


# ======================================================================== Materials

CHAR = (40, 42, 47)      # the racks' paint
GRAPH = (54, 56, 60)     # UPS, tape library
OFFW = (196, 192, 178)   # the CRAC's enamel
RED = (150, 36, 30)


def px_set(img, x, y, c):
    w, h = img.size
    img.load()[x % w, y % h] = tuple(int(round(max(0, min(255, v)))) for v in c[:3]) + (255,)


def materials():
    # Painted steel of the racks: matte charcoal with a few worn spots; a panelled side with its seam and screws
    save(M.grime(M.painted_metal(401, base=CHAR, panel=False, chips=3, mottle=2, grain=2, under=(92, 94, 96)), 0.05, 402), "rk-paint")
    save(M.grime(M.painted_metal(403, base=shade3(CHAR, 1.08), panel=True, chips=2, mottle=2, grain=2, under=(92, 94, 96), screws=True), 0.06, 404, bias="bottom"), "rk-side")
    # The perforated door: 1 px holes (cut out), staggered row by row (a fine hex perforation), each
    # hole's lower lip lit
    mesh = M.painted_metal(405, base=shade3(CHAR, 1.12), panel=False, chips=2, under=(90, 92, 94))
    M.grime(mesh, 0.06, 406)
    p = mesh.load()
    # (round 4, after the first shots: a hole every 4 px, rows 2 px apart and staggered by 2, a diamond lattice with more
    # land round each hole, as a perforated sheet; a 2 px checker read as a coarse grille close to)
    holes = [(x + (2 if (y // 2) % 2 else 0), y) for y in range(0, S, 2) for x in range(0, S, 4)]
    for (x, y) in holes:
        M.touch(mesh, x % S, (y + 1) % S, 0.05)
    for (x, y) in holes:
        p[x % S, y] = (0, 0, 0, 0)
    save(cutout(mesh), "rk-mesh")
    # The cabinet's inside (seen through the door and where a unit is missing)
    void = M.noise_hv((14, 15, 18), 2, 407, mottle=2)
    save(void, "rk-void")
    # Mounting rails: zinc, a column of square holes
    rail = M.galvanised(408, base=(120, 124, 126), spangle=8)
    for y in range(0, S, 4):
        for x in (2, 3):
            for dy in (1, 2):
                px_set(rail, x + 8 * 0, y + dy, (16, 16, 18))
                px_set(rail, x + 16, y + dy, (16, 16, 18))
    save(rail, "rk-rail")
    # Top: vent perforations, a brush strip for the cables
    top = M.painted_metal(409, base=CHAR, panel=True, chips=2, under=(90, 92, 94))
    for y in range(4, 28, 3):
        for x in range(4, 14, 2):
            px_set(top, x, y, (14, 14, 16))
    for y in range(6, 26):
        for x in range(19, 28):
            px_set(top, x, y, (10, 10, 12) if (x + y) % 2 else (26, 26, 28))
    save(M.grime(top, 0.18, 410, color=(96, 90, 80)), "rk-top")
    save(M.brushed_metal(411, base=(150, 152, 156), streak=7, sheen=8), "rk-chrome")
    save(M.rubber(412, base=(24, 24, 26)), "rk-black")
    # Cables, muted: each a loom of strands along its length (vertical), a tie every 8 px
    for name, c in (("cb-blue", (54, 70, 104)), ("cb-grey", (112, 112, 108)), ("cb-yellow", (138, 118, 52)), ("cb-black", (30, 30, 32)),
                    ("cb-red", (112, 46, 40)), ("cb-green", (58, 92, 62)), ("cb-white", (170, 168, 160))):
        img = M.noise_hv(c, 3, sum(map(ord, name)), mottle=3)
        for x in range(0, S, 2):
            for y in range(S):
                M.touch(img, x, y, -0.12)
        for y in range(5, S, 8):
            for x in range(S):
                px_set(img, x, y, (24, 24, 24))
        save(img, name)
    # The asset label on the top rail: an aged white strip, a line of small print and a short barcode, read at 2 px high
    lab = Image.new("RGBA", (32, 32), (186, 182, 166, 255))
    rng = random.Random(413)
    d = ImageDraw.Draw(lab)
    for y0 in range(0, 32, 2):
        for x in range(1, 31):
            if (x < 14 and rng.random() < 0.55) or (x >= 16 and x % 2 == 0):
                d.point((x, y0 + 1), fill=(70, 68, 62, 255) if x < 14 else (40, 40, 40, 255))
    save(M.grime(lab, 0.12, 414), "rk-label")
    leds()
    server_faces()
    server_backs()


def shade3(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def leds():
    for name, c in (("rk-led-green", (110, 255, 130)), ("rk-led-amber", (255, 180, 60)), ("rk-led-blue", (100, 170, 255)),
                    ("rk-led-red", (255, 70, 60)), ("rk-led-dead", (44, 50, 46))):
        img = Image.new("RGBA", (32, 32), c + (255,))
        if name != "rk-led-dead":
            for y in range(32):
                for x in range(32):
                    dd = math.hypot(x - 15.5, y - 15.5) / 22
                    px_set(img, x, y, shade3(c, 1.1 - 0.35 * dd))
        save(img, name)


def server_faces():
    """The fronts of the units, 20 px wide (10 units), one design per band of rows:
        0-1   1U server: ear, four drive slots, vents          2-3   1U blank (vented)
        4-7   2U server: eight SFF caddies, a vent, its badge  8-11  2U server: 3.5" bays
        12-19 4U server: a grille over a drive cage            20-23 2U switch: 2 x 12 ports
        24-25 1U patch panel: 24 ports, a label strip          26-27 1U cable manager: a brush slot
        28-31 2U disk shelf: 12 upright 3.5" caddies (the storage array)
    and to the right (x 20-31) small parts: a caddy face, a port, labels."""
    img = Image.new("RGBA", (32, 32), (20, 20, 22, 255))
    rng = random.Random(420)

    def band(y0, h, base):
        for y in range(y0, y0 + h):
            for x in range(20):
                px_set(img, x, y, M.lift(base, rng.uniform(-3, 3)))
        for x in range(20):
            M.touch(img, x, y0, 0.22)
            M.touch(img, x, y0 + h - 1, -0.25)
        for y in range(y0, y0 + h):
            M.touch(img, 0, y, 0.15)
            M.touch(img, 19, y, -0.2)

    silver, dark = (118, 120, 124), (44, 46, 50)
    # 1U server
    band(0, 2, silver)
    for x in (1, 18):
        px_set(img, x, 0, (170, 172, 176))
    for i in range(4):
        for x in range(3 + i * 3, 5 + i * 3):
            px_set(img, x, 1, (22, 22, 24))
    for x in range(16, 18):
        px_set(img, x, 1, (30, 32, 30))
    # 1U blank, vented
    band(2, 2, dark)
    for x in range(2, 18, 2):
        px_set(img, x, 3, (14, 14, 16))
    # 2U SFF
    band(4, 4, silver)
    for i in range(8):
        x = 2 + i * 2
        px_set(img, x, 5, (60, 62, 66)); px_set(img, x, 6, (60, 62, 66))
        px_set(img, x + 1, 5, (26, 26, 28)); px_set(img, x + 1, 6, (26, 26, 28))
    for x in range(1, 19):
        px_set(img, x, 7, (90, 92, 96))
    # 2U LFF bays
    band(8, 4, (72, 74, 80))
    for i in range(4):
        x = 2 + i * 4
        for dx in range(3):
            px_set(img, x + dx, 9, (34, 36, 40)); px_set(img, x + dx, 10, (50, 52, 56))
        px_set(img, x + 2, 10, (150, 150, 150))
    # 4U: a bezel with a mesh grille over the drive cage
    band(12, 8, (36, 38, 42))
    for y in range(13, 19):
        for x in range(2, 15):
            if (x + y) % 2 == 0:
                px_set(img, x, y, (14, 14, 16))
    for y in range(14, 18):
        px_set(img, 17, y, (98, 100, 104))
    px_set(img, 16, 13, (150, 150, 150))
    # 2U switch: 2 x 12 ports
    band(20, 4, (30, 32, 36))
    for r_ in (21, 22):
        for i in range(8):
            x = 2 + i * 2
            px_set(img, x, r_, (8, 8, 8))
    for y in (21, 22):
        px_set(img, 18, y, (60, 62, 60))
    # 1U patch panel
    band(24, 2, (34, 36, 40))
    for i in range(9):
        px_set(img, 1 + i * 2, 25, (8, 8, 8))
    for x in range(1, 19):
        px_set(img, x, 24, (190, 188, 176) if x % 5 else (34, 36, 40))
    # 1U cable manager: a brush slot
    band(26, 2, (26, 26, 28))
    for x in range(1, 19):
        px_set(img, x, 27, (8, 8, 10) if x % 2 else (20, 20, 22))
    # 2U disk shelf: 12 upright caddies
    band(28, 4, (58, 60, 66))
    for i in range(9):
        x = 1 + i * 2
        for y in (29, 30):
            px_set(img, x, y, (92, 94, 100))
        px_set(img, x, 31, (24, 26, 28))
    # Small parts at the right: a caddy (20-23, 0-7), an RJ port block (24-27, 0-3), a yellow label (28-31, 0-3)
    for y in range(8):
        for x in range(20, 24):
            px_set(img, x, y, (96, 98, 104) if x < 23 else (40, 42, 46))
    px_set(img, 21, 6, (160, 160, 160))
    save(img, "rk-srv")


def server_backs():
    """The rear of the units: PSUs with their fan grilles and power inlets, I/O ports, all dark and calm."""
    img = M.noise_hv((26, 28, 32), 2, 430, mottle=2)
    rng = random.Random(431)
    for y0 in range(0, 32, 4):
        for x in range(32):
            M.touch(img, x, y0, 0.15)
            M.touch(img, x, y0 + 3, -0.2)
        # Two PSUs at the left: a fan circle and a socket
        for k, x0 in enumerate((1, 7)):
            for yy in (1, 2):
                for xx in range(x0, x0 + 3):
                    px_set(img, xx, y0 + yy, (12, 12, 14) if (xx + yy) % 2 else (46, 48, 52))
            px_set(img, x0 + 4, y0 + 1, (60, 60, 60))
            px_set(img, x0 + 4, y0 + 2, (8, 8, 8))
        # Ports
        for xx in range(14, 28, 2):
            if rng.random() < 0.7:
                px_set(img, xx, y0 + 1, (8, 8, 10))
        px_set(img, 29, y0 + 2, (70, 110, 70) if rng.random() < 0.3 else (40, 44, 40))
    save(img, "rk-srvback")


# ======================================================================== The rack

# A unit stack: (kind, height in units) from the bottom; kinds index server_faces' bands
BANDS = {"1u": (0, 1), "blank": (2, 1), "2u": (4, 2), "2ul": (8, 2), "4u": (12, 4), "sw": (20, 2), "patch": (24, 1), "mgr": (26, 1),
         "shelf": (28, 2)}


def stack_for(kind, part, seed):
    rng = random.Random(f"{kind}-{part}-{seed}")
    out = []
    top = 15.0 if part == "lower" else 13.0
    y = 2.75 if part == "lower" else 0.0
    while True:
        if kind == "srv":
            u = rng.choice(("1u", "1u", "2u", "2u", "2ul", "4u", "blank", "gap"))
        elif kind == "store":
            u = rng.choice(("shelf", "shelf", "shelf", "2u", "blank")) if part == "lower" or y > 3 else "shelf"
        else:  # net
            u = rng.choice(("patch", "mgr", "sw", "patch", "sw", "gap", "1u"))
        h = 1.0 if u == "gap" else BANDS[u][1] * 1.0
        if y + h > top:
            break
        out.append((u, y, h))
        y += h
    return out


def led(name, x, y, lit, colour="rk-led-green"):
    return b(name, (x, y, 2.25), (x + 0.5, y + 0.5, 2.5), colour if lit else "rk-led-dead", faces=N_, glow=255 if lit else 0)


def rack_elements(part, state):
    """One block of a rack (front north). The pair of blocks share every x/z coordinate, so their parts meet."""
    gutted = state == "gutted"
    kind = "store" if state.startswith("store") else "net" if state.startswith("net") else "srv"
    lit = state in ("leda", "ledb", "both", "storelit", "netlit")
    door = kind == "srv" and not gutted
    lower = part == "lower"
    y0, y1 = 0.0, 16.0
    els = [
        # Carcass: the side panels (full depth), the inside back of the cabinet, the plinth or the top cap
        b("SideW", (0, y0, 0.75), (0.75, y1, 15.25), {"side": "rk-side", "front": "rk-paint", "back": "rk-paint", "top": "rk-paint", "bottom": "rk-paint"},
          faces=("west", "north", "south")),
        b("SideE", (15.25, y0, 0.75), (16, y1, 15.25), {"side": "rk-side", "front": "rk-paint", "back": "rk-paint", "top": "rk-paint", "bottom": "rk-paint"},
          faces=("east", "north", "south")),
        b("RailL", (2, y0, 2.5), (3, y1, 3), "rk-rail", faces=("north", "east")),
        b("RailR", (13, y0, 2.5), (14, y1, 3), "rk-rail", faces=("north", "west")),
        b("Inside", (0.75, y0, 13.5), (15.25, y1, 14), "rk-void", faces=N_),
    ]
    if lower:
        els += [b("Plinth", (0.75, 0, 1.25), (15.25, 1.25, 14.75), {"front": "rk-black", "back": "rk-black", "side": "rk-black", "top": "rk-paint"},
                  faces=("north", "south")),
                b("FootW", (0.25, 0, 0.5), (1.5, 0.5, 1.75), "rk-black", faces=("north", "west", "up")),
                b("FootE", (14.5, 0, 0.5), (15.75, 0.5, 1.75), "rk-black", faces=("north", "east", "up")),
                b("Sill", (0.75, 1.25, 1.25), (15.25, 2.75, 2.5), "rk-paint", faces=("north", "up"))]
    else:
        els += [b("Cap", (0, 15, 0.5), (16, 16, 15.5), {"top": "rk-top", "side": "rk-paint", "front": "rk-paint", "back": "rk-paint"},
                  faces=("up", "north", "south", "east", "west")),
                b("Header", (0.75, 13, 1.25), (15.25, 15, 2.5), "rk-paint", faces=("north", "down")),
                uvb("Label", (6, 13.75, 1.1), (10, 14.75, 1.25), "rk-label", (0, 0, 4, 1)),
                b("Brush", (6, 16, 9), (12, 16.25, 12), "rk-black", faces=("up", "north", "south", "east", "west"))]

    # The units on their rails
    if not gutted:
        rng = random.Random(f"leds-{part}-{state}")
        for i, (u, uy, h) in enumerate(stack_for(kind, part, 1)):
            if u == "gap":
                continue
            v0, vh = BANDS[u]
            depth = 13.5 if u not in ("patch", "mgr") else 6
            els.append(uvb(f"U{i}", (3, uy, 2.5), (13, uy + h, depth), "rk-srv", (0, v0 / 2, 10, (v0 + vh * 2) / 2)))
            if u in ("1u", "2u", "2ul", "4u", "sw", "shelf"):
                on = lit and rng.random() < 0.75
                colour = {"ledb": "rk-led-amber", "both": "rk-led-blue", "storelit": "rk-led-blue"}.get(state, "rk-led-green")
                if on and rng.random() < 0.08:
                    colour = "rk-led-amber" if colour != "rk-led-amber" else "rk-led-red"
                els.append(led(f"L{i}", 11.5, uy + h - 0.75, on, colour))
                if u in ("sw", "shelf"):
                    els.append(led(f"M{i}", 5 + rng.choice((0, 1, 2)), uy + 0.25, lit and rng.random() < 0.6, colour))
        if kind == "net":
            els += patch_cords(part, lit)
    else:
        els += gutted_insides(part)

    # The front door: stiles, a rail, the perforated panel, two hinges, the swing handle
    if door:
        dz0, dz1 = 0.25, 1.0
        els += [
            b("StileL", (0.75, y0, dz0), (2.25, y1 - (2 if not lower else 0), dz1), "rk-paint", faces=("north", "west", "east")),
            b("StileR", (13.75, y0, dz0), (15.25, y1 - (2 if not lower else 0), dz1), "rk-paint", faces=("north", "east", "west")),
        ]
        if lower:
            els += [b("RailB", (2.25, 1.25, dz0), (13.75, 2.75, dz1), "rk-paint", faces=("north", "up")),
                    b("Mesh", (2.25, 2.75, 0.6), (13.75, 16, 0.7), "rk-mesh", faces=N_),
                    b("Hinge0", (0.5, 4, 0.0), (1.25, 6, 0.75), "rk-black", faces=("north", "west", "up", "down")),
                    b("HandleBase", (14.05, 10.5, 0.0), (14.95, 15, 0.25), "rk-black", faces=("north", "east", "west", "up", "down")),
                    b("Handle", (14.2, 11, -0.6), (14.8, 14.5, 0.0), "rk-black", faces=("north", "east", "west", "up", "down")),
                    b("Lock", (14.25, 14.6, -0.15), (14.75, 15.1, 0.0), "rk-chrome", faces=("north", "up"))]
        else:
            els += [b("RailT", (0.75, 13, dz0), (15.25, 15, dz1), "rk-paint", faces=("north", "down", "east", "west")),
                    b("Mesh", (2.25, 0, 0.6), (13.75, 13, 0.7), "rk-mesh", faces=N_),
                    b("Hinge1", (0.5, 9, 0.0), (1.25, 11, 0.75), "rk-black", faces=("north", "west", "up", "down")),
                    uvb("DoorLabel", (6, 13.75, 0.1), (10, 14.75, 0.25), "rk-label", (0, 2, 4, 3))]
            # (the asset label sits on the door's top rail when there is a door)
            els = [e for e in els if e["name"] != "Label"]
    elif kind != "srv" or gutted:
        # No door: the front of the frame (the posts the door would hang on)
        els += [b("PostL", (0.75, y0, 1.25), (2, y1 - (2 if not lower else 0), 2.5), "rk-paint", faces=("north", "east")),
                b("PostR", (14, y0, 1.25), (15.25, y1 - (2 if not lower else 0), 2.5), "rk-paint", faces=("north", "west"))]

    # The rear: the units' backs, cable looms down the back, a PDU strip, the perforated rear door over them
    rng = random.Random(f"rear-{part}-{state}")
    if not gutted:
        els.append(b("Backs", (3, y0 if not lower else 2.75, 13.5), (13, y1 - (3 if not lower else 0), 14), "rk-srvback", faces=("south",)))
    els += [
        b("PDU", (12.5, y0 if not lower else 2, 14), (13.75, y1 - (3 if not lower else 0), 14.75), "rk-black", faces=("south", "west", "east")),
    ]
    looms = [("cb-blue", 3.2), ("cb-grey", 5.2), ("cb-black", 7.4)] if kind != "net" else [("cb-blue", 3.2), ("cb-yellow", 5.0), ("cb-grey", 7.0), ("cb-blue", 9.0)]
    for j, (t, x) in enumerate(looms):
        if gutted and j > 0:
            break
        w = rng.uniform(1.2, 1.7)
        els.append(b(f"Loom{j}", (x, y0, 14.0 + 0.1 * j), (x + w, y1, 14.9), t, faces=("south", "east", "west")))
    dz0, dz1 = 15.0, 15.75
    els += [
        b("RStileL", (0.75, y0, dz0), (2.25, y1 - (2 if not lower else 0), dz1), "rk-paint", faces=("south", "west", "east")),
        b("RStileR", (13.75, y0, dz0), (15.25, y1 - (2 if not lower else 0), dz1), "rk-paint", faces=("south", "east", "west")),
        b("RMesh", (2.25, y0 if not lower else 1.25, 15.3), (13.75, y1 - (2 if not lower else 0), 15.4), "rk-mesh", faces=("south",)),
    ]
    if lower:
        els.append(b("RHandle", (1.2, 11, 15.75), (1.8, 14.5, 16.3), "rk-black", faces=("south", "east", "west", "up", "down")))
    else:
        els.append(b("RRailT", (0.75, 13, dz0), (15.25, 15, dz1), "rk-paint", faces=("south", "down")))
    return els


def patch_cords(part, lit):
    """Patch cords from the panels' ports to the cable managers at the sides of a network rack, in loops."""
    rng = random.Random("cords-" + part)
    els = []
    for i in range(7):
        y = rng.uniform(3.5, 14.5) if part == "lower" else rng.uniform(1, 12)
        x = rng.uniform(4, 11)
        t = rng.choice(("cb-blue", "cb-blue", "cb-yellow", "cb-grey", "cb-white", "cb-red"))
        side = rng.choice((-1, 1))
        xe = 2.5 if side < 0 else 13.5
        a, c = sorted((x, xe))
        # A cord drooping toward the manager: a little turned about z
        els.append(b(f"Cord{i}", (a, y - 0.2, 1.7 + 0.1 * (i % 3)), (c, y + 0.2, 2.1 + 0.1 * (i % 3)), t, faces=("north", "up", "down"),
                     rot=(0, 0, side * rng.uniform(2, 5)), origin=(x, y, 2)))
        els.append(b(f"Plug{i}", (x - 0.3, y - 0.3, 1.9), (x + 0.3, y + 0.3, 2.5), t, faces=("north", "east", "west", "up")))
    # The side managers: black fingers with the cords running down inside them
    for k, x in enumerate((1.0, 13.75)):
        els.append(b(f"Mgr{k}", (x, 0, 1.0), (x + 1.25, 16, 2.4), "rk-black", faces=("north", "east", "west")))
        els.append(b(f"MgrCords{k}", (x + 0.25, 0, 0.9), (x + 1.0, 16, 1.0), rng.choice(("cb-blue", "cb-yellow")), faces=N_))
    return els


def gutted_insides(part):
    """A gutted rack: the bays empty but for a unit pulled half out on its rails, wires hanging down the front, the door
    hanging open off its lower hinge, turned toward the aisle."""
    rng = random.Random("gut-" + part)
    els = []
    if part == "lower":
        els.append(uvb("Pulled", (3, 7, -3.5), (13, 9, 9), "rk-srv", (0, 2, 10, 4), faces=("north", "up", "east", "west"), rest="rk-paint"))
        els.append(b("RailsOut", (3.2, 6.6, -3.5), (12.8, 7, 2.5), "rk-chrome", faces=("up", "east", "west")))
        els.append(uvb("Last", (3, 2.75, 2.5), (13, 4.75, 13.5), "rk-srv", (0, 4, 10, 6)))
    else:
        els.append(uvb("Last", (3, 9, 2.5), (13, 10, 13.5), "rk-srv", (0, 1, 10, 2)))
    for i, (t, x) in enumerate((("cb-blue", rng.uniform(4, 6)), ("cb-grey", rng.uniform(8, 10)), ("cb-yellow", rng.uniform(10.5, 12)))):
        top = 16 if part == "lower" else rng.uniform(9, 13)
        bot = 2.75 if part == "lower" else 0
        els.append(b(f"Wire{i}", (x, bot, 2.0 + 0.2 * i), (x + 0.5, top, 2.5 + 0.2 * i), t, faces=("north", "east", "west")))
    # The door, swung out about its hinge (x 0.75, z 0.25) and sagging
    leaf_top = 16 if part == "lower" else 14
    els += [
        b("Door", (0.75, 0 if part == "upper" else 1.25, 0.25), (15.25, leaf_top, 0.6), "rk-paint", faces=("north", "south", "east", "up"),
          rot=(0, 40, 0), origin=(0.75, 8, 0.25)),
        b("DoorMesh", (2.25, 2.75 if part == "lower" else 0, 0.05), (13.75, leaf_top - (1 if part == "upper" else 0), 0.25), "rk-mesh", faces=("north",),
          rot=(0, 40, 0), origin=(0.75, 8, 0.25)),
    ]
    return els


SUPERSEDED = ["battery-front", "battery-upper", "bucket", "conduit", "crac-lower", "crac-open", "crac-side", "crac-upper", "crt-case",
              "desk-frame", "desk-top", "duct", "extinguisher", "keyboard", "led-amber", "led-blue", "led-dead", "led-green", "panel-pdu",
              "rack-back", "rack-gutted", "rack-top", "screen-glitch", "screen-lit", "sign-exit-dead", "sign-exit-lit", "tray-mesh",
              "tray-rod", "ups-lower", "ups-open", "ups-side", "ups-upper", "window-frame", "window-glass"] + [f"rowend-{c}" for c in "abcdefgh"]

RACK_STATES4 = ["off", "leda", "ledb", "both", "gutted", "store", "storelit", "net", "netlit"]


def rack_blocktype():
    shapes = {}
    for part in ("lower", "upper"):
        for state in RACK_STATES4:
            base = shape(f"l120-rack-{part}-{state}", rack_elements(part, state))
            for s in SIDES:
                shapes[f"l120-rack-{part}-{state}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    # (Darker than the prototype: a lit rack is a small pool of light in a dark room, not a lamp)
    light = {"*-upper-leda-*": [21, 6, 3], "*-upper-ledb-*": [7, 6, 3], "*-upper-both-*": [30, 5, 4], "*-upper-storelit-*": [30, 5, 3],
             "*-upper-netlit-*": [21, 6, 3]}
    json_block("l120-rack", [{"code": "part", "states": ["lower", "upper"]}, {"code": "state", "states": RACK_STATES4}] + [{"code": "side", "states": SIDES}], shapes,
               "Level 120: a server rack, two blocks high (lower, upper), its front to the side. Servers behind a perforated door, dark or "
               "their LEDs on (leda green, ledb amber, both green and blue); a storage array of disk shelves (store, storelit); a network "
               "rack of patch panels, switches and patch cords (net, netlit); or gutted, its door hanging off. A lit upper block gives a "
               "little light. Salvage: copper wire, brackets, now and then a circuit board",
               {"collisionbox": cuboid(FULL), "selectionbox": cuboid(FULL)},
               extra={"lightHsvByType": light, "dropsByType": {
                   "*-lower-gutted-*": drops(("scrapwire", 0.2, 0.2), ("metalbracket", 0.5, 0.4)),
                   "*-upper-gutted-*": drops(("scrapwire", 0.15, 0.15)),
                   "*-lower-*": drops(("scrapwire", 0.3, 0.25), ("metalbracket", 0.5, 0.4), ("l3999-circuitboard", 0.1, 0)),
                   "*-upper-*": drops(("scrapwire", 0.2, 0.2), ("l3999-circuitboard", 0.075, 0)),
               }}, inventory="l120-rack-lower-leda-north")


def main():
    materials()
    rack_blocktype()
    import gen_120_r4_props
    gen_120_r4_props.main()
    walldeco_overrides()
    # The round-2/3 textures this round's models no longer use (gen_120 and gen_120_detail still paint them first)
    for name in SUPERSEDED:
        f = os.path.join(TEX, name + ".png")
        if os.path.exists(f):
            os.remove(f)
    print("Level 120 round 4: assets rebuilt")



# ======================================================================== The wall dressing, round 4

def _shared(path):
    """A shared shape of the mod's: its elements and its texture table (keys prefixed x- so they never meet ours)."""
    import json as _json
    import re as _re
    root = os.path.join(os.path.dirname(__file__), "..", "assets", "backrooms", "shapes", path + ".json")
    d = _json.loads(_re.sub(r"^\s*//.*$", "", open(root, encoding="utf-8").read(), flags=_re.M))
    for k, v in d["textures"].items():
        EXTERN["x-" + k] = v if ":" in v else "backrooms:" + v
    els = []
    for e in d["elements"]:
        for f in e["faces"].values():
            f["texture"] = "#x-" + f["texture"][1:]
        els.append(e)
    return els


def walldeco_overrides():
    """Rewrites some of gen_120_detail's wall dressings: the EXIT sign and the fire point as the released levels' own (on
    our wall), the wall of screens as framed panels on a rail, round conduit with couplings and straps, the electrical panel
    as a cabinet with its door."""
    from gen_120_detail import wall
    out = {}
    for lit in (False, True):
        out["exit-lit" if lit else "exit-dead"] = [
            b("Housing", (2, 3, -2.5), (14, 11, 0), "x-exithousing", faces=("north", "east", "west", "up", "down")),
            uvb("Face", (2.4, 3.4, -2.6), (13.6, 10.6, -2.5), "x-exitface", (0, 4, 16, 12), glow=200 if lit else 0)]
    ext = [e for e in _shared("block/detail/l1deco-extinguisher") if e["name"] not in ("Wall", "Sign")]
    out["fire-lower"] = ext
    for look in ("dead", "glitch", "smashed"):
        tex = {"dead": "mon-dead", "glitch": "mon-glitch", "smashed": "screen-smashed"}[look]
        for part in ("lower", "upper"):
            y0, y1 = (2.5, 16) if part == "lower" else (0, 13.5)
            els = [b("Rail", (0, 7, -0.4), (16, 8, 0), "arm-grey", faces=("north", "up", "down")),
                   b("BezelT", (0.5, y1 - 0.75, -1.4), (15.5, y1, -0.4), "mon-black", faces=("north", "up", "down", "east", "west")),
                   b("BezelB", (0.5, y0, -1.4), (15.5, y0 + 0.75, -0.4), "mon-black", faces=("north", "up", "down", "east", "west")),
                   b("BezelL", (0.5, y0 + 0.75, -1.4), (1.25, y1 - 0.75, -0.4), "mon-black", faces=("north", "east", "west")),
                   b("BezelR", (14.75, y0 + 0.75, -1.4), (15.5, y1 - 0.75, -0.4), "mon-black", faces=("north", "east", "west")),
                   uvb("Panel", (1.25, y0 + 0.75, -1.2), (14.75, y1 - 0.75, -1.1), tex, (0, 0, 16, 16), glow=140 if look == "glitch" else 0),
                   b("Back", (1.25, y0 + 0.75, -1.1), (14.75, y1 - 0.75, -0.4), "mon-black", faces=("east", "west"))]
            if part == "lower":
                els.append(b("Logo", (7.25, y0 + 0.2, -1.45), (8.75, y0 + 0.5, -1.4), "arm-grey", faces=N_))
            out[f"screens-{look}-{part}"] = els
    con = []
    for i, (y, r) in enumerate(((11.7, 0.7), (9.3, 0.5))):
        z = -0.2 - r - 0.1
        con += [b(f"Pipe{i}A", (0, y - r, z - r * 0.45), (16, y + r, z + r * 0.45), "rk-chrome", faces=("north", "up", "down")),
                b(f"Pipe{i}B", (0, y - r * 0.45, z - r), (16, y + r * 0.45, z + r), "rk-chrome", faces=("north", "up", "down")),
                b(f"Coupling{i}", (0, y - r - 0.15, z - r - 0.15), (1.0, y + r + 0.15, z + r * 0.45), "du-galv", faces=("north", "up", "down", "east", "west")),
                b(f"Strap{i}", (8, y - r - 0.1, z - r - 0.1), (8.75, y + r + 0.1, 0), "du-galv", faces=("north", "up", "down", "east", "west"))]
    out["conduit"] = con
    out["panel"] = [
        b("Box", (3, 1, -1.75), (13, 14, 0), "dk-steel", faces=("east", "west", "up", "down")),
        b("Door", (3.25, 1.25, -2.0), (12.75, 13.75, -1.75), "dk-drawer", faces=("north", "east", "west", "up", "down")),
        b("HingeA", (2.75, 3, -2.0), (3.25, 5, -1.5), "rk-chrome", faces=("north", "west", "up", "down")),
        b("HingeB", (2.75, 10, -2.0), (3.25, 12, -1.5), "rk-chrome", faces=("north", "west", "up", "down")),
        b("Latch", (11, 6.5, -2.6), (11.75, 8.5, -2.0), "rk-black", faces=("north", "east", "west", "up", "down")),
        uvb("Card", (5, 9.5, -2.1), (9, 12, -2.0), "pl-hv", (0, 0, 16, 16)),
        b("Holder", (5, 3, -2.15), (10, 7.5, -2.0), "pl-ups", faces=N_, uv=(0, 8, 16, 16)),
        b("Conduit", (7.4, 14, -1.3), (8.6, 16, -0.1), "rk-chrome", faces=("north", "east", "west")),
        b("Lock", (11.1, 9, -2.2), (11.6, 9.5, -2.0), "rk-chrome", faces=N_),
    ]
    # Cables down the wall: five looms of muted colours in a bundle, tied every half block, held by a clamp at the top and
    # fanning out over the floor at the foot
    for part in ("lower", "mid", "upper"):
        els = []
        for i, (x, t) in enumerate(((5.5, "cb-black"), (6.6, "cb-blue"), (7.7, "cb-grey"), (8.8, "cb-blue"), (9.9, "cb-black"))):
            y0 = 0.5 if part == "lower" else 0
            els.append(b(f"C{i}", (x, y0, -1.4 + 0.15 * (i % 2)), (x + 1, 16, -0.2), t, faces=("north", "east", "west")))
            if part == "lower":
                els.append(b(f"F{i}", (x, 0, -3 - i * 0.6), (x + 1, 0.5, -0.2), t, faces=("up", "east", "west", "north")))
        for y in ((4, 12) if part != "lower" else (6, 13)):
            els.append(b(f"Tie{y}", (5.3, y, -1.6), (11, y + 0.5, -0.1), "rk-black", faces=("north", "east", "west", "up", "down")))
        if part == "upper":
            els += [b("Clamp", (4.5, 13, -2), (11.5, 14, 0), "lr-galv", faces=("north", "east", "west", "up", "down")),
                    b("Bolt0", (5, 13.25, -2.2), (5.5, 13.75, -2), "rk-chrome", faces=N_),
                    b("Bolt1", (10.5, 13.25, -2.2), (11, 13.75, -2), "rk-chrome", faces=N_)]
        out[f"cables-{part}"] = els
    for kind, els in out.items():
        base = "wall-base"
        shape(f"l120-walldeco-{kind}", [wall(base)] + els)


if __name__ == "__main__":
    main()
