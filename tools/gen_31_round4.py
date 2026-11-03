"""Level 31, "Roller Rink": round 4's asset-quality pass (2026-11-02). Run it AFTER gen_31.py, gen_31_props.py and
gen_31_round3.py: it rebuilds some of their blocks to the round's bar (same block codes, so the layout does not move;
it overwrites their shape, texture and blocktype files) and adds a few new ones.

Rebuilt (codes kept):  l31-skateshelf (real skates in two-by-three cubbies), l31-djdesk (deck, mixer: a booth fascia
    with lit strips, a turntable, a mixer between CD decks), l31-speaker (a PA stack), l31-truss (a laced box truss with
    par cans on yokes), l31-discoball (the mirror ball's shape), l31-rinkwood's textures, l31-retrocab (1980s uprights
    in the classic profile), l31-photobooth, l31-dispenser (the green-card machine), l31-cinemabench, l31-mediacab,
    l31-riser's shape (nosing and aisle lights), l31-table, l31-stall, l31-vanity, l31-jukebox; and round 3's wall mounts get
    their depth: the neon signs' tubes stand proud of their boards, the big TV gets a bezel, the dryer a real body
New:  l31-barrier (the rink's barrier: a thin padded wall along the boards' outer edge; straight, corner and post
    pieces, chosen by WorldGenerator.L31.Round4.cs from the neighbours), l31-rinkgate (the gaps' gates: a hinge post
    with a leaf swung open into the rink, left or right, or the sill between), l31-pinball (in place of Level 3999's in
    the arcade), l31-slushie (the snack counters' slushie machine), l31-popcorn (in place of Level Fun's popcorn cart),
    l31-locker (the rink's coin lockers, in place of Level 52's school lockers)
Reused from other levels, placed by the layout: Level 120's CRAC units in the HVAC rooms, Level 36's queue posts in
    Skate Rental.

Every oriented prop is modelled facing NORTH (its front at low z) with the variant group "side" last: -east is
rotateY 270, -south 180, -west 90. Run from the repo root:  bash tools/locked.sh run python tools/gen_31_round4.py
"""
import math
import os
import random

from PIL import Image, ImageDraw

import matlib as M
from modelkit import DIRS, without, turn
from texlib import S
from gen_31 import write_json, shape, save, SIDES, TEX, BLOCKS, STONE, WOOD, CLOTH
from gen_31_props import B, prop_block, METAL, text, ctext, GAMES

ROT = {"north": 0, "east": 270, "south": 180, "west": 90}
SIDE4 = ("north", "east", "south", "west")
K8 = math.tan(math.radians(22.5))  # an octagon's half edge over its apothem


def rgba(c, a=255):
    return tuple(c[:3]) + (a,)


def save_tex(img, name):
    """Saves a texture after making every texel fully opaque or fully clear (the opaque pass tints alpha 1-254)."""
    px = img.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255 if a >= 128 else 0)
    save(img, name)


# ======================================================================== Geometry helpers

def octo(name, c, r, lo, hi, axis, tex, glow=0, ends=True, k=K8, faces_end=("up", "down")):
    """An octagonal prism of four boxes (two crossed bands and the same two turned 45 degrees) round `axis` ("x", "y"
    or "z") through `c` (the two cross-plane coordinates in x, y, z order with the axis left out), from lo to hi along
    the axis. The end faces come from the first band only; the others stop a hair short so the ends do not z-fight."""
    w = r * k
    out = []
    for i, (a, b, rot) in enumerate(((r, w, 0), (w, r, 0), (r, w, 45), (w, r, 45))):
        e = 0.0 if i == 0 else 0.02 * i
        l0, l1 = lo + e, hi - e
        if axis == "y":
            frm, to, rr = (c[0] - a, l0, c[1] - b), (c[0] + a, l1, c[1] + b), (0, rot, 0)
            endf = ("up", "down")
        elif axis == "z":
            frm, to, rr = (c[0] - a, c[1] - b, l0), (c[0] + a, c[1] + b, l1), (0, 0, rot)
            endf = ("north", "south")
        else:
            frm, to, rr = (l0, c[0] - a, c[1] - b), (l1, c[0] + a, c[1] + b), (rot, 0, 0)
            endf = ("east", "west")
        faces = DIRS if (ends and i == 0) else without(DIRS, *endf)
        out.append(B(f"{name}{i}", frm, to, tex, faces=faces, glow=glow, rot=rr if rot else None))
    return out


def disc_tex(name, size, ring_fn):
    """A round picture on a clear background: ring_fn(d) gives the colour (or None) at distance d (0 at the centre, 1
    at the rim) for a size x size texture; outside the rim is clear (alpha 0), so a flat box shows a disc."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = img.load()
    h = size / 2.0
    for y in range(size):
        for x in range(size):
            d = math.hypot(x + 0.5 - h, y + 0.5 - h) / h
            if d <= 1.0:
                c = ring_fn(d, x, y)
                if c is not None:
                    px[x, y] = rgba(c)
    save_tex(img, name)


FULL = (0, 0, 16, 16)


def mirror_x(els):
    """The elements mirrored left to right (x -> 16 - x); for unturned boxes and turns about y or z."""
    out = []
    for e in els:
        e = dict(e)
        (x1, y1, z1), (x2, y2, z2) = e["from"], e["to"]
        e["from"], e["to"] = [round(16 - x2, 4), y1, z1], [round(16 - x1, 4), y2, z2]
        f = dict(e["faces"])
        f["east"], f["west"] = f.get("west"), f.get("east")
        e["faces"] = {k: v for k, v in f.items() if v is not None}
        if "rotationOrigin" in e:
            o = e["rotationOrigin"]
            e["rotationOrigin"] = [round(16 - o[0], 4), o[1], o[2]]
            for a in ("rotationY", "rotationZ"):
                if a in e:
                    e[a] = -e[a]
        out.append(e)
    return out


# ======================================================================== Materials

def materials():
    save_tex(M.brushed_metal(seed=4101, base=(200, 204, 210), sheen=18), "r4-chrome")
    save_tex(M.brushed_metal(seed=4102, base=(160, 164, 170), sheen=10), "r4-alu")
    blk = M.noise_hv((36, 36, 40), 2, 4103, S, 3, (8, 4))
    save_tex(M.grime(blk, 0.06, 4104, color=(20, 20, 20)), "r4-black")
    save_tex(M.painted_metal(seed=4105, base=(42, 42, 46), panel=False, chips=3, under=(120, 120, 124)), "r4-blackmetal")
    save_tex(M.fabric(seed=4106, base=(30, 30, 33), weave="twill", contrast=8), "r4-tolex")
    save_tex(M.rubber(seed=4107, base=(28, 28, 30)), "r4-rubber")
    # Speaker grille: black perforated steel
    g = M.noise_hv((26, 26, 28), 2, 4108, S, 2, (8, 8))
    gp = g.load()
    for y in range(1, S, 2):
        for x in range((y // 2) % 2, S, 2):
            gp[x, y] = (8, 8, 9, 255)
    save_tex(g, "r4-grille")
    # Vinyl padding: navy, stitched seams, a soft sheen along the length
    pad = M.noise_hv((40, 46, 104), 3, 4109, S, 4, (8, 4))
    pp = pad.load()
    for y in range(S):
        for x in range(S):
            r, g_, b, a = pp[x, y]
            k = 1 + 0.16 * math.exp(-((y - 9) / 4.0) ** 2)
            if y in (2, 29) and x % 3 != 2:
                k *= 0.7  # the stitching
            pp[x, y] = (M.clamp(r * k), M.clamp(g_ * k), M.clamp(b * k), 255)
    save_tex(pad, "r4-pad")
    mag = M.noise_hv((176, 44, 132), 3, 4110, S, 3, (8, 4))
    mp = mag.load()
    for y in range(S):
        for x in range(S):
            r, g_, b, a = mp[x, y]
            k = 1 + 0.18 * math.exp(-((y - 10) / 4.0) ** 2)
            if y in (3, 28) and x % 3 != 2:
                k *= 0.72
            mp[x, y] = (M.clamp(r * k), M.clamp(g_ * k), M.clamp(b * k), 255)
    save_tex(mag, "r4-padpink")
    # The barrier's rink face: white HDPE, scuffed black by skates near its foot; and its skirt face: rink carpet
    hd = M.noise_hv((232, 232, 228), 2, 4111, S, 2, (8, 4))
    rng = random.Random(4112)
    hp = hd.load()
    for _ in range(40):
        x, y = rng.randrange(S), rng.randrange(18, S)
        ln = rng.randint(2, 6)
        for i in range(ln):
            xx = (x + i) % S
            r, g_, b, a = hp[xx, y]
            hp[xx, y] = (M.clamp(r * 0.55), M.clamp(g_ * 0.55), M.clamp(b * 0.56), 255)
    M.grime(hd, 0.18, 4113, color=(90, 88, 84), bias="bottom", cover=0.5)
    save_tex(hd, "r4-hdpe")
    out = M.carpet(seed=4114, base=(30, 28, 44), tone2=(60, 30, 80), mix2=0.25, pile=8)
    save_tex(M.grime(out, 0.12, 4115, color=(16, 16, 20), bias="bottom"), "r4-barrier-out")


# ======================================================================== Skates and the rental cubbies

def skate_textures():
    for n, base, stitch in (("tan", (176, 120, 70), (236, 214, 170)), ("white", (230, 228, 222), (150, 40, 60)),
                            ("black", (40, 38, 40), (200, 200, 200))):
        img = M.noise_hv(base, 3, 4120 + len(n), S, 4, (8, 4))
        px = img.load()
        for x in range(S):
            for y in range(S):
                r, g, b, a = px[x, y]
                if y >= 27:
                    px[x, y] = rgba((34, 30, 28))  # the sole's welt
                elif y in (4, 24) and x % 2 == 0:
                    px[x, y] = rgba(stitch)
        M.grime(img, 0.14, 4124 + len(n), color=(80, 66, 50), bias="bottom")
        save_tex(img, "r4-boot-" + n)
        # The laces: a padded tongue with criss-cross laces (stretched over a small face)
        t = M.noise_hv(tuple(int(v * 0.92) for v in base), 2, 4127 + len(n), S, 2, (8, 4))
        d = ImageDraw.Draw(t)
        for k in range(5):
            y = 3 + k * 6
            d.line([(6, y), (26, y + 5)], fill=rgba((246, 244, 236)), width=2)
            d.line([(26, y), (6, y + 5)], fill=rgba((246, 244, 236)), width=2)
            d.rectangle([4, y, 6, y + 1], fill=rgba((200, 200, 204)))
            d.rectangle([26, y, 28, y + 1], fill=rgba((200, 200, 204)))
        save_tex(t, "r4-laces-" + n)
    for n, c in (("orange", (244, 132, 36)), ("yellow", (246, 214, 40)), ("pink", (240, 90, 176)), ("teal", (40, 200, 190)),
                 ("red", (214, 40, 46))):
        hub = (214, 216, 222)

        def ring(d, x, y, c=c, hub=hub):
            if d < 0.32:
                return hub if d > 0.14 else (90, 92, 98)
            k = 1.0 - 0.25 * (d - 0.32)
            return tuple(int(v * k) for v in c) if d < 0.9 else tuple(int(v * 0.7) for v in c)
        disc_tex("r4-wheel-" + n, 16, ring)
        # The tread seen edge on: two wheels with the truck's dark gap between
        tr = M.noise_hv(tuple(int(v * 0.85) for v in c), 2, 4129, S, 2, (8, 4))
        save_tex(tr, "r4-tread-" + n)
    ts = M.rubber(seed=4130, base=(196, 40, 70))
    save_tex(ts, "r4-toestop")
    save_tex(M.wood_planks(seed=4131, base=(214, 180, 128), planks=2, direction="h", grain=3, flecks=0.4), "r4-birch")
    save_tex(M.wood_planks(seed=4132, base=(170, 136, 92), planks=1, direction="v", grain=3, flecks=0.4), "r4-birchback")
    # Size tags for the cubbies
    for k, s in enumerate(("6", "7", "8", "9", "10", "11")):
        img = Image.new("RGBA", (32, 32), rgba((246, 244, 232)))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 31, 15], outline=rgba((40, 40, 48)))
        ctext(img, 16, 3, s, (30, 30, 40), sx=2)
        save_tex(img, "r4-tag" + s)


def skate(tag, cx, y0, z0, yaw, boot, wheel, laces=True):
    """One quad skate, heel toward north (z0) and toe into the cubby, its centre line at x=cx, turned `yaw` degrees
    about its own centre: wheels and trucks, the plate, the boot and its shaft, the tongue and laces, a toe stop."""
    o = (cx, y0 + 2.0, z0 + 2.5)
    rot = (0, yaw, 0) if yaw else None
    x0 = cx - 0.85
    b = "r4-boot-" + boot
    els = []
    for ax, (za, zb) in (("R", (0.6, 1.7)), ("F", (3.1, 4.2))):
        for side, (xa, xb) in (("L", (x0 - 0.1, x0 + 0.5)), ("R", (x0 + 1.2, x0 + 1.8))):
            els.append(B(f"{tag}W{ax}{side}", (xa, y0, z0 + za), (xb, y0 + 1.1, z0 + zb), "r4-tread-" + wheel, rot=rot, origin=o,
                         east=("r4-wheel-" + wheel, FULL), west=("r4-wheel-" + wheel, FULL)))
    els += [
        B(f"{tag}Plate", (x0 + 0.3, y0 + 0.9, z0 + 0.4), (x0 + 1.4, y0 + 1.25, z0 + 4.4), "r4-alu", rot=rot, origin=o,
          faces=without(DIRS, "up")),
        B(f"{tag}Foot", (x0 + 0.1, y0 + 1.25, z0 + 0.3), (x0 + 1.6, y0 + 2.35, z0 + 4.6), b, rot=rot, origin=o,
          faces=without(DIRS, "down")),
        B(f"{tag}Shaft", (x0 + 0.05, y0 + 2.35, z0 + 0.15), (x0 + 1.65, y0 + 3.9, z0 + 2.3), b, rot=rot, origin=o,
          faces=without(DIRS, "down"), up=("r4-black", None)),
        B(f"{tag}Tongue", (x0 + 0.3, y0 + 2.35, z0 + 2.3), (x0 + 1.4, y0 + 3.2, z0 + 3.7), b, rot=rot, origin=o,
          faces=without(DIRS, "down", "north"), up=("r4-laces-" + boot, FULL), south=("r4-laces-" + boot, FULL)),
        B(f"{tag}Stop", (x0 + 0.45, y0 + 0.3, z0 + 4.4), (x0 + 1.25, y0 + 1.3, z0 + 5.0), "r4-toestop", rot=rot, origin=o),
    ]
    return els


def skateshelf():
    """A rental cubby block: birch ply, two columns by three rows, a pair of skates heel-out in each cubby (one empty),
    a size tag on the shelf edge under each."""
    els = [
        B("SideL", (0, 0, 0), (0.75, 16, 15.5), "r4-birch"),
        B("SideR", (15.25, 0, 0), (16, 16, 15.5), "r4-birch"),
        B("Back", (0.75, 0, 15.5), (15.25, 16, 16), "r4-birchback"),
        B("Plinth", (0.75, 0, 0.6), (15.25, 1.0, 15.5), "r4-black", faces=without(DIRS, "down")),
    ]
    shelves = [(1.0, 1.6), (5.9, 6.5), (10.8, 11.4), (15.4, 16.0)]
    for i, (a, b) in enumerate(shelves):
        els.append(B(f"Shelf{i}", (0.75, a, 0), (15.25, b, 15.5), "r4-birch", faces=without(DIRS, "east", "west")))
    for r in range(3):
        a, b = shelves[r][1], shelves[r + 1][0]
        els.append(B(f"Div{r}", (7.7, a, 0), (8.3, b, 15.5), "r4-birch", faces=without(DIRS, "up", "down")))
    rng = random.Random(4140)
    boots = ["tan", "tan", "white", "black", "tan", "white"]
    wheels = ["orange", "yellow", "pink", "teal", "red", "orange"]
    sizes = [["11", "10"], ["9", "8"], ["7", "6"]]
    for r in range(3):
        y0 = shelves[r][1]
        for c, (xa, xb) in enumerate(((0.75, 7.7), (8.3, 15.25))):
            m = (xa + xb) / 2
            els.append(B(f"Tag{r}{c}", (m - 1.2, y0 - 0.55, -0.12), (m + 1.2, y0 - 0.02, 0), "r4-birch",
                         faces=("north",), north=("r4-tag" + sizes[r][c], (0, 0, 16, 8))))
            if (r, c) == (1, 1):
                continue  # rented out
            k = r * 2 + c
            for s, sx in enumerate((-1.55, 1.55)):
                yaw = (-12 if s == 0 else 12) + rng.uniform(-4, 4)
                els += skate(f"S{r}{c}{s}", m + sx, y0, 0.9 + rng.uniform(0, 0.8), yaw, boots[k], wheels[k])
    return shape("l31-skateshelf", els)


# ======================================================================== The rink's barrier and gates

# Each layer of the barrier: (name, y1, y2, z1, z2, texture spec); z runs from the skirt side (0) into the rink
BARRIER = [
    ("Shoe", 0.0, 1.5, 0.2, 3.8, "r4-rubber"),
    ("Body", 1.5, 13.0, 0.5, 3.5, {"front": "r4-barrier-out", "back": "r4-hdpe", "side": "r4-hdpe", "top": "r4-hdpe", "bottom": "r4-hdpe"}),
    ("Bumper", 6.0, 8.6, 3.5, 5.0, "r4-pad"),
    ("Cap", 13.0, 15.3, 0.0, 4.5, "r4-pad"),
    ("Crown", 15.3, 16.0, 0.6, 3.9, "r4-padpink"),
]


def _layer(name, x1, x2, y1, y2, z1, z2, tex):
    return B(name, (x1, y1, z1), (x2, y2, z2), tex)


def barrier_straight():
    els = [_layer(n, 0, 16, y1, y2, z1, z2, t) for n, y1, y2, z1, z2, t in BARRIER]
    # (a chrome joint strip between panels on the rink side, and a nose on the bumper)
    els.append(B("Joint", (0, 1.5, 3.5), (0.6, 13, 3.75), "r4-chrome", faces=without(DIRS, "north")))
    els.append(B("Nose", (0, 6.5, 5.0), (16, 8.1, 5.4), "r4-pad", faces=without(DIRS, "north")))
    return els


def barrier_corner():
    """The north wall and the west wall: each layer of the north wall from its own inner depth, the west wall's from
    beyond the north wall's, so no two faces overlap."""
    els = []
    for n, y1, y2, z1, z2, t in BARRIER:
        els.append(_layer(n + "N", z1, 16, y1, y2, z1, z2, t))
        els += turn([_layer(n + "W", 0, 16 - z2, y1, y2, z1, z2, t)], 3)
    els.append(B("NoseN", (5.0, 6.5, 5.0), (16, 8.1, 5.4), "r4-pad", faces=without(DIRS, "north")))
    els += turn([B("NoseW", (0, 6.5, 5.0), (11.0, 8.1, 5.4), "r4-pad", faces=without(DIRS, "north"))], 3)
    return els


def barrier_post():
    """The square where a north wall ending at this block's west edge meets a west wall ending at its north edge."""
    els = []
    for n, y1, y2, z1, z2, t in BARRIER:
        els.append(_layer(n + "A", 0, z2, y1, y2, z1, z2, t))
        if z1 > 0:
            els.append(_layer(n + "B", z1, z2, y1, y2, 0, z1, t))
    els.append(B("Nose", (0, 6.5, 5.0), (5.4, 8.1, 5.4), "r4-pad"))
    els.append(B("NoseB", (5.0, 6.5, 0), (5.4, 8.1, 5.0), "r4-pad"))
    return els


def gate_leaf():
    """A gap's end: a padded hinge post capping the barrier, and the gate leaf on two hinges swung open into the rink."""
    els = [
        B("Post", (0, 0, 0), (2.2, 15.3, 4.5), "r4-hdpe", north=("r4-barrier-out", None)),
        B("PostCap", (-0.01, 15.3, -0.01), (2.4, 16.4, 4.7), "r4-padpink"),
        B("Leaf", (0.9, 1.6, 4.5), (1.7, 13.0, 14.5), "r4-hdpe"),
        B("LeafPad", (0.6, 13.0, 4.5), (2.0, 14.6, 14.8), "r4-pad"),
        B("LeafKick", (0.85, 1.5, 4.5), (1.75, 3.6, 14.6), "r4-rubber"),
        B("Latch", (1.7, 8.0, 13.2), (2.2, 9.4, 14.2), "r4-chrome"),
        B("Hinge1", (1.7, 3.5, 4.2), (2.4, 5.0, 5.0), "r4-chrome"),
        B("Hinge2", (1.7, 10.5, 4.2), (2.4, 12.0, 5.0), "r4-chrome"),
        B("Sill", (2.2, 0, 0), (16, 0.35, 4.0), "r4-alu", faces=without(DIRS, "down")),
    ]
    return els


def gate_sill():
    return [B("Sill", (0, 0, 0), (16, 0.35, 4.0), "r4-alu", faces=without(DIRS, "down")),
            B("Strip", (0, 0.35, 1.6), (16, 0.45, 2.4), "r4-rubber", faces=without(DIRS, "down"))]


# ======================================================================== The DJ booth

def dj_textures():
    # The fascia: black laminate with a faint diagonal sheen
    f = M.noise_hv((22, 20, 26), 2, 4150, S, 2, (8, 4))
    fp = f.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = fp[x, y]
            k = 1 + 0.18 * math.exp(-(((x - y) % S - 16) / 3.0) ** 2)
            fp[x, y] = (M.clamp(r * k), M.clamp(g * k), M.clamp(b * k), 255)
    save_tex(f, "r4-fascia")
    # Lit strips (emissive), bright in the middle of the strip
    for n, c in (("cyan", (70, 230, 255)), ("pink", (255, 70, 200)), ("amber", (255, 180, 60))):
        img = Image.new("RGBA", (S, S), rgba(c))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 12, 31, 19], fill=rgba(tuple(min(255, v + 90) for v in c)))
        save_tex(img, "r4-led-" + n)
    # A record on the platter (seen from above), a CD deck's jog wheel
    disc_tex("r4-record", 32, lambda d, x, y: (230, 60, 60) if d < 0.26 else (240, 230, 220) if d < 0.3 else
             ((18, 18, 20) if int(d * 40) % 3 else (34, 34, 38)) if d < 0.96 else (60, 60, 64))
    disc_tex("r4-slipmat", 32, lambda d, x, y: (20, 20, 24) if d < 0.9 else (150, 154, 160))
    disc_tex("r4-jog", 32, lambda d, x, y: (90, 92, 98) if d > 0.86 else (36, 36, 40) if d > 0.3 else (160, 164, 170))
    # The mixer's face: channel strips, EQ rows, VU ladders printed on brushed metal
    mx = M.brushed_metal(seed=4151, base=(58, 60, 66), sheen=8)
    d = ImageDraw.Draw(mx)
    for ch in range(3):
        x = 5 + ch * 9
        d.line([(x, 14), (x, 28)], fill=rgba((10, 10, 12)), width=1)
        for y in (3, 6, 9):
            d.point((x - 2, y), fill=rgba((220, 220, 224)))
    d.line([(10, 30), (22, 30)], fill=rgba((10, 10, 12)))
    save_tex(mx, "r4-mixer")
    cd = M.noise_hv((40, 40, 46), 2, 4152, S, 2, (8, 4))
    d = ImageDraw.Draw(cd)
    d.rectangle([4, 2, 27, 4], fill=rgba((12, 12, 14)))  # the disc slot
    d.rectangle([4, 7, 15, 10], fill=rgba((40, 120, 200)))  # the display
    d.rectangle([5, 8, 12, 9], fill=rgba((160, 230, 255)))
    for k, c in enumerate(((60, 220, 90), (240, 170, 40), (230, 60, 60))):
        d.rectangle([4 + k * 5, 27, 7 + k * 5, 29], fill=rgba(c))
    save_tex(cd, "r4-cdtop")
    vu = Image.new("RGBA", (8, 16), rgba((10, 10, 12)))
    d = ImageDraw.Draw(vu)
    for y in range(1, 15, 2):
        c = (240, 60, 50) if y < 4 else (250, 200, 40) if y < 7 else (70, 240, 90)
        d.rectangle([1, y, 6, y], fill=rgba(c))
    save_tex(vu, "r4-vu")


def dj_body():
    return [
        B("Carcass", (0, 0, 2.0), (16, 14, 14.5), "r4-black", faces=without(DIRS, "north", "up", "down")),
        B("Fascia", (0, 0.8, 1.0), (16, 14, 2.0), "r4-fascia", faces=without(DIRS, "south")),
        B("Kick", (0, 0, 1.4), (16, 0.8, 2.0), "r4-rubber", faces=without(DIRS, "south", "down")),
        B("LedHi", (0, 11.2, 0.6), (16, 11.9, 1.0), "r4-led-cyan", glow=230, faces=without(DIRS, "south")),
        B("LedLo", (0, 2.2, 0.6), (16, 2.7, 1.0), "r4-led-pink", glow=230, faces=without(DIRS, "south")),
        B("Top", (0, 14, 0.5), (16, 15, 15.0), "r4-black", faces=without(DIRS, "down")),
        B("Lip", (0, 14, 0.2), (16, 15.3, 0.5), "r4-alu"),
    ]


def djdesk_deck():
    els = dj_body() + [
        B("Plinth", (1.5, 15, 2.5), (14.5, 16.6, 13.5), "r4-alu", up=("r4-black", None)),
        B("PlinthFeet", (1.8, 15, 2.8), (14.2, 15.4, 13.2), "r4-rubber", faces=("north", "east", "south", "west")),
    ]
    els += octo("Platter", (7.0, 8.0), 4.6, 16.6, 17.4, "y", "r4-alu", ends=False)
    els += [
        B("Record", (2.4, 17.4, 3.4), (11.6, 17.55, 12.6), "r4-black", faces=("up",), up=("r4-record", FULL)),
        B("Spindle", (6.85, 17.55, 7.85), (7.15, 18.0, 8.15), "r4-chrome", faces=without(DIRS, "down")),
        B("ArmBase", (12.0, 16.6, 10.6), (13.4, 17.6, 12.0), "r4-chrome"),
        B("Arm", (12.45, 17.6, 4.8), (12.95, 18.0, 11.4), "r4-chrome", rot=(0, 18, 0), origin=(12.7, 17.8, 11.3)),
        B("Shell", (12.05, 17.3, 4.0), (13.25, 17.9, 5.2), "r4-black", rot=(0, 18, 0), origin=(12.7, 17.8, 11.3)),
        B("Weight", (12.2, 17.5, 11.4), (13.2, 18.4, 12.6), "r4-black"),
        B("Pitch", (13.2, 16.6, 4.0), (14.0, 16.7, 9.0), "r4-black", faces=("up",)),
        B("PitchCap", (13.1, 16.6, 6.0), (14.1, 17.1, 6.8), "r4-alu", faces=without(DIRS, "down")),
        B("Start", (2.0, 16.6, 11.6), (3.4, 16.9, 13.0), "r4-alu", faces=without(DIRS, "down")),
        B("StrobeDot", (2.2, 16.6, 3.0), (2.8, 16.95, 3.6), "r4-led-pink", glow=200, faces=without(DIRS, "down")),
    ]
    return shape("l31-djdesk-deck", els)


def djdesk_mixer():
    els = dj_body() + [
        B("Mixer", (4.5, 15, 3.0), (11.5, 16.8, 13.0), "r4-blackmetal", up=("r4-mixer", FULL)),
    ]
    for ch in range(3):
        x = 5.7 + ch * 2.2
        els.append(B(f"Fader{ch}", (x - 0.4, 16.8, 7.2 - ch * 0.6), (x + 0.4, 17.4, 8.0 - ch * 0.6), "r4-alu"))
        for k in range(2):
            els.append(B(f"Knob{ch}{k}", (x - 0.35, 16.8, 10.3 + k * 1.3), (x + 0.35, 17.3, 11.0 + k * 1.3), "r4-black",
                         up=("r4-alu", None)))
    els += [
        B("Xfade", (7.4, 16.8, 3.6), (8.6, 17.3, 4.4), "r4-alu"),
        B("VuL", (10.3, 16.8, 6.0), (10.7, 16.95, 12.0), "r4-black", faces=("up",), up=("r4-vu", FULL), glow=200),
        B("VuR", (10.9, 16.8, 6.0), (11.3, 16.95, 12.0), "r4-black", faces=("up",), up=("r4-vu", FULL), glow=200),
    ]
    # Two CD decks either side of the mixer, jog wheels up
    for k, x in enumerate((0.6, 12.2)):
        els += [B(f"Cd{k}", (x, 15, 3.5), (x + 3.2, 16.6, 12.5), "r4-blackmetal", up=("r4-cdtop", FULL)),
                B(f"Jog{k}", (x + 0.3, 16.6, 6.8), (x + 2.9, 16.75, 9.4), "r4-black", faces=("up",), up=("r4-jog", FULL))]
    # Headphones left on the desk's corner
    els += [B("CupL", (13.0, 15, 13.0), (14.2, 15.8, 14.4), "r4-black"),
            B("CupR", (14.8, 15, 13.0), (16.0, 15.8, 14.4), "r4-black"),
            B("Band", (13.4, 15.8, 13.5), (15.6, 16.2, 13.9), "r4-alu")]
    return shape("l31-djdesk-mixer", els)


def speaker_textures():
    def cone(d, x, y):
        if d > 0.9:
            return (24, 24, 26)  # the surround's roll
        if d > 0.84:
            return (60, 60, 64)
        k = 0.6 + 0.4 * d
        return tuple(int(v * k) for v in (70, 70, 76)) if int(d * 18) % 2 else tuple(int(v * k) for v in (60, 60, 66))
    disc_tex("r4-cone", 32, cone)
    disc_tex("r4-dustcap", 16, lambda d, x, y: (40, 40, 44) if d > 0.8 else (64, 64, 70))
    h = Image.new("RGBA", (S, S), rgba((20, 20, 22)))
    d = ImageDraw.Draw(h)
    for k in range(6):
        d.rectangle([2 + k * 2, 3 + k, 29 - k * 2, 28 - k], outline=rgba((30 + k * 6,) * 3))
    d.rectangle([13, 13, 18, 18], fill=rgba((6, 6, 6)))
    save_tex(h, "r4-horn")
    logo = M.noise_hv((26, 26, 28), 2, 4160, S, 2, (8, 8))
    d = ImageDraw.Draw(logo)
    d.rectangle([8, 12, 23, 18], fill=rgba((180, 184, 190)))
    text(logo, 10, 13, "PRO", (20, 20, 24))
    save_tex(logo, "r4-badge")


def speaker():
    """A PA stack: a sub cabinet with an 18-inch cone, a top cabinet with a 12-inch cone and a horn, steel corners,
    handles and a cable down the back; 30 units tall."""
    els = [
        B("Sub", (1, 0.4, 1.2), (15, 13.4, 15), "r4-tolex", faces=without(DIRS, "down")),
        B("Skid", (1.4, 0, 1.6), (14.6, 0.4, 14.6), "r4-rubber", faces=without(DIRS, "down", "up")),
        B("SubBaffle", (1.6, 1.0, 0.9), (14.4, 12.8, 1.2), "r4-black", faces=without(DIRS, "south")),
        B("SubCone", (2.4, 1.4, 0.75), (13.6, 12.4, 0.9), "r4-black", faces=("north",), north=("r4-cone", FULL)),
        B("SubCap", (6.8, 5.8, 0.6), (9.2, 8.0, 0.75), "r4-black", faces=("north",), north=("r4-dustcap", FULL)),
        B("Top", (2, 13.8, 2.0), (14, 30, 14.5), "r4-tolex", faces=without(DIRS, "down")),
        B("TopBaffle", (2.5, 14.3, 1.7), (13.5, 29.5, 2.0), "r4-black", faces=without(DIRS, "south")),
        B("TopCone", (3.6, 15.0, 1.55), (12.4, 23.8, 1.7), "r4-black", faces=("north",), north=("r4-cone", FULL)),
        B("TopCap", (7.0, 18.4, 1.4), (9.0, 20.4, 1.55), "r4-black", faces=("north",), north=("r4-dustcap", FULL)),
        B("Horn", (4.2, 24.4, 1.4), (11.8, 28.8, 1.7), "r4-black", faces=("north",), north=("r4-horn", FULL)),
        B("HornLipT", (4.0, 28.8, 1.2), (12.0, 29.2, 1.7), "r4-alu", faces=without(DIRS, "south")),
        B("HornLipB", (4.0, 24.0, 1.2), (12.0, 24.4, 1.7), "r4-alu", faces=without(DIRS, "south")),
        B("Badge", (12.0, 25.6, 1.5), (13.2, 26.4, 1.7), "r4-black", faces=("north",), north=("r4-badge", (6, 10, 18, 20))),
        B("Cable", (7.6, 0, 15), (8.4, 30, 15.5), "r4-rubber", faces=without(DIRS, "north", "down")),
    ]
    # Steel corner protectors on the front corners of both cabinets, recessed handles on the sides
    for k, (x1, x2, y1, y2, z) in enumerate(((1, 15, 0.4, 13.4, 1.2), (2, 14, 13.8, 30, 2.0))):
        for cx in (x1, x2 - 1.2):
            for cy in (y1, y2 - 1.2):
                els.append(B(f"Corner{k}{cx}{cy}", (cx - 0.1, cy - 0.05, z - 0.25), (cx + 1.3, cy + 1.25, z + 1.2), "r4-chrome"))
        hy = (y1 + y2) / 2 + 2
        els += [B(f"HandleW{k}", (x1 - 0.3, hy, 6), (x1, hy + 1.0, 10), "r4-chrome", faces=without(DIRS, "east")),
                B(f"HandleE{k}", (x2, hy, 6), (x2 + 0.3, hy + 1.0, 10), "r4-chrome", faces=without(DIRS, "west"))]
    return shape("l31-speaker", els)


# ======================================================================== The lighting rig

def truss():
    """A box truss of aluminium tube along X: four chords, zig-zag lacing on both sides and underneath (turned tubes),
    a cable loom, and two par cans on clamps and yokes, tilted toward the boards, lenses lit."""
    els = []
    ya, yb, za, zb = 12.0, 15.0, 5.5, 10.5
    t = 0.55
    for i, (y, z) in enumerate(((ya, za), (ya, zb), (yb, za), (yb, zb))):
        els.append(B(f"Chord{i}", (0, y, z), (16, y + t, z + t), "r4-alu", faces=without(DIRS, "east", "west")))
    # Lacing: on each vertical face, diagonals rising and falling every 4 units; underneath, the same in plan
    ang = math.degrees(math.atan2(yb - ya, 4.0))
    ln = math.hypot(yb - ya, 4.0)
    for side, z in (("N", za), ("S", zb)):
        for k in range(4):
            cx = 2 + k * 4
            a = ang if k % 2 == 0 else -ang
            els.append(B(f"Lace{side}{k}", (cx - ln / 2, (ya + yb + t) / 2 - 0.2, z + 0.08), (cx + ln / 2, (ya + yb + t) / 2 + 0.2, z + t - 0.08),
                         "r4-alu", rot=(0, 0, a), faces=("north", "south", "up", "down")))
    angp = math.degrees(math.atan2(zb - za, 4.0))
    lnp = math.hypot(zb - za, 4.0)
    for k in range(4):
        cx = 2 + k * 4
        a = angp if k % 2 == 0 else -angp
        els.append(B(f"LaceU{k}", (cx - lnp / 2, ya + 0.08, (za + zb + t) / 2 - 0.2), (cx + lnp / 2, ya + t - 0.08, (za + zb + t) / 2 + 0.2),
                     "r4-alu", rot=(0, a, 0), faces=("north", "south", "up", "down")))
    els.append(B("Loom", (0, yb + t, 7.6), (16, yb + t + 0.5, 8.4), "r4-rubber", faces=without(DIRS, "east", "west")))
    # Par cans: a clamp on the bottom chord, a yoke, the can tilted out over the boards, the lens lit
    for k, (x, lens, tilt) in enumerate(((4, "pink", 22), (12, "cyan", -22))):
        zc = za if tilt > 0 else zb + t
        o = (x, 8.9, 8.0)
        els += [
            B(f"Clamp{k}", (x - 0.6, ya - 0.9, zc - 0.5), (x + 0.6, ya + 0.1, zc + 0.5), "r4-black"),
            B(f"Stem{k}", (x - 0.25, ya - 1.6, 7.75), (x + 0.25, ya - 0.9, 8.25), "r4-black"),
            B(f"YokeT{k}", (x - 2.3, ya - 2.1, 7.7), (x + 2.3, ya - 1.6, 8.3), "r4-black"),
            B(f"YokeL{k}", (x - 2.3, 8.0, 7.7), (x - 1.8, ya - 2.1, 8.3), "r4-black"),
            B(f"YokeR{k}", (x + 1.8, 8.0, 7.7), (x + 2.3, ya - 2.1, 8.3), "r4-black"),
            B(f"CanA{k}", (x - 1.75, 6.4, 7.2), (x + 1.75, 9.8, 8.8), "r4-blackmetal", rot=(tilt, 0, 0), origin=o),
            B(f"CanB{k}", (x - 0.8, 6.42, 6.25), (x + 0.8, 9.78, 9.75), "r4-blackmetal", rot=(tilt, 0, 0), origin=o,
              faces=without(DIRS, "up", "down")),
            B(f"CanC{k}", (x - 1.35, 6.44, 6.65), (x + 1.35, 9.76, 9.35), "r4-blackmetal", rot=(tilt, 0, 0), origin=o,
              faces=without(DIRS, "up", "down")),
            B(f"Lens{k}", (x - 1.6, 6.3, 6.4), (x + 1.6, 6.4, 9.6), "r4-black", rot=(tilt, 0, 0), origin=o,
              faces=("down",), down=("truss-lens-" + lens, FULL, 255)),
            B(f"Gel{k}", (x - 1.9, 6.0, 6.1), (x + 1.9, 6.4, 6.4), "r4-black", rot=(tilt, 0, 0), origin=o),
        ]
    return shape("l31-truss", els)


def ball_textures():
    img = Image.new("RGBA", (S, S))
    px = img.load()
    rng = random.Random(4170)
    tints = [(250, 250, 255), (210, 214, 226), (160, 166, 184), (120, 126, 150), (255, 140, 220), (130, 230, 255), (235, 235, 245)]
    for cy in range(0, S, 4):
        for cx in range(0, S, 4):
            c = rng.choice(tints) if rng.random() < 0.85 else (70, 74, 90)
            for y in range(cy, cy + 4):
                for x in range(cx, cx + 4):
                    edge = x == cx or y == cy
                    k = 0.55 if edge else (1.06 if (x - cx) + (y - cy) < 3 else 1.0)
                    px[x, y] = rgba(tuple(M.clamp(v * k) for v in c))
    save_tex(img, "r4-facets")


def discoball():
    """The mirror ball: five faceted octagonal rings stacked into a ball 10 units across, on a drop rod from a motor
    box under the ceiling; the facets glow a little (they catch the pin-spots)."""
    els = [
        B("Motor", (6.2, 14.8, 6.2), (9.8, 16, 9.8), "r4-blackmetal", faces=without(DIRS, "up")),
        B("Rod", (7.7, 13.6, 7.7), (8.3, 14.8, 8.3), "r4-chrome", faces=without(DIRS, "up", "down")),
        B("Collar", (7.2, 13.0, 7.2), (8.8, 13.6, 8.8), "r4-chrome"),
    ]
    for i, (y1, y2, r) in enumerate(((0.4, 2.4, 3.4), (2.4, 4.7, 5.6), (4.7, 8.7, 6.8), (8.7, 11.0, 5.6), (11.0, 13.0, 3.4))):
        els += octo(f"Ring{i}", (8, 8), r, y1, y2, "y", "r4-facets", glow=110)
    return shape("l31-discoball", els)


# ======================================================================== The rink's boards

def rinkwood():
    """Maple strips, 4 px wide, with grain, staggered butt joints, a varnish sheen and the grey arcs of skate wheels;
    the lane stripe and the centre's painted swirl as inlays worn at the edges."""
    def boards(seed):
        img = M.wood_planks(seed=seed, base=(214, 170, 112), planks=8, direction="h", grain=3, contrast=0.8, joints=0.6,
                            flecks=0.3, per_plank=12, gap=(120, 86, 52))
        px = img.load()
        rng = random.Random(seed + 1)
        for y in range(S):
            for x in range(S):
                r, g, b, a = px[x, y]
                k = 1 + 0.10 * math.exp(-((((x + 2 * y) % S) - 16) / 6.0) ** 2)
                px[x, y] = (M.clamp(r * k), M.clamp(g * k), M.clamp(b * k), 255)
        for _ in range(3):  # wheel scuffs, long faint arcs along the boards
            y0, x0, ln = rng.randrange(S), rng.randrange(S), rng.randint(8, 18)
            for i in range(ln):
                x, y = (x0 + i) % S, (y0 + int(1.5 * math.sin(i / 5.0))) % S
                r, g, b, a = px[x, y]
                px[x, y] = (M.clamp(r * 0.86), M.clamp(g * 0.86), M.clamp(b * 0.88), 255)
        return img
    magenta, cyan = (226, 60, 170), (60, 200, 230)
    save_tex(boards(4180), "rinkwood-plain")
    for name, vertical in (("rinkwood-stripens", True), ("rinkwood-stripewe", False)):
        img = boards(4181 if vertical else 4182)
        px = img.load()
        rng = random.Random(4183)
        for i in range(S):
            for j in range(13, 19):
                x, y = (j, i) if vertical else (i, j)
                c = magenta if j not in (13, 18) else (250, 250, 246)
                if rng.random() < 0.08:
                    continue  # worn through to the wood
                px[x, y] = rgba(tuple(M.clamp(v * (1.12 if j in (15, 16) else 1.0)) for v in c))
        save_tex(img, name)
    img = boards(4184)
    px = img.load()
    rng = random.Random(4185)
    for y in range(S):
        for x in range(S):
            v = math.sin(2 * math.pi * (x + 2 * y) / S + 1.5 * math.sin(2 * math.pi * (x - y) / S))
            c = magenta if v > 0.35 else cyan if v < -0.35 else (124, 70, 200)
            if rng.random() < 0.06:
                continue
            r, g, b, a = px[x, y]
            k = 0.82 + 0.25 * (r / 255.0)  # the boards' grain shows through the paint
            px[x, y] = rgba(tuple(M.clamp(cv * k) for cv in c))
    save_tex(img, "rinkwood-centre")


# ======================================================================== The arcade

def cab_art(g, d):
    """Side art for an upright: the body colour, a bold diagonal band and stars in the accent, scuffed at the foot."""
    img = M.painted_metal(seed=4200 + len(g), base=d["body"], panel=False, chips=3, under=(60, 60, 64))
    dr = ImageDraw.Draw(img)
    acc = rgba(d["accent"])
    dr.polygon([(0, 20), (31, 6), (31, 12), (0, 26)], fill=acc)
    dr.polygon([(0, 27), (31, 13), (31, 15), (0, 29)], fill=rgba(tuple(int(v * 0.6) for v in d["accent"])))
    for (x, y) in ((6, 6), (22, 24), (12, 13)):
        dr.point([(x, y), (x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], fill=rgba((255, 255, 255)))
    M.grime(img, 0.16, 4210 + len(g), color=(20, 20, 22), bias="bottom", cover=0.4)
    save_tex(img, "r4-cabart-" + g)


def retrocab(g, d):
    """A 1980s upright: side panels in the classic profile with T-moulding, a kick plate, a coin door with lit coin
    returns, a sloped control panel (ball-top stick, three buttons), the CRT recessed in its bezel, a speaker grille,
    the lit marquee; 30 units tall."""
    art = "r4-cabart-" + g
    acc = "r4-led-" + ("cyan" if g == "shooter" else "amber")
    els = [
        B("Lower", (2, 0, 4), (14, 13, 15), art, north=("r4-black", None)),
        B("Kick", (2.2, 0, 3.7), (13.8, 1.6, 4), "r4-blackmetal", faces=without(DIRS, "south")),
        B("Door", (4.5, 3.5, 3.7), (11.5, 11.0, 4), "r4-black", faces=without(DIRS, "south"), north=("cab-coin", (3.0, 5.4, 9.0, 12.0))),
        B("CoinL", (5.6, 8.3, 3.4), (6.8, 9.7, 3.7), "r4-black", faces=without(DIRS, "south"), north=("cab-red", None, 220)),
        B("CoinR", (9.2, 8.3, 3.4), (10.4, 9.7, 3.7), "r4-black", faces=without(DIRS, "south"), north=("cab-red", None, 220)),
        B("Panel", (2, 12.2, 0.8), (14, 14.6, 6.0), "r4-blackmetal", rot=(-10, 0, 0), origin=(8, 13.4, 6.0),
          up=("cab-panel-" + g, (0, 0, 12, 2.5))),
        B("Mid", (2, 13, 6.4), (14, 25, 15), art, north=("r4-black", None)),
        B("Bezel", (2.6, 14.6, 5.6), (13.4, 24.2, 6.4), "r4-black", faces=without(DIRS, "south")),
        B("Screen", (3.6, 15.4, 5.35), (12.4, 23.4, 5.6), "r4-black", faces=("north",), north=("cab-screen-" + g, (0, 0, 9, 7.5), 170)),
        B("Grille", (3.0, 24.2, 4.6), (13.0, 25.2, 6.4), "r4-grille", faces=without(DIRS, "south")),
        B("Marquee", (2.2, 25.2, 3.9), (13.8, 29.4, 4.6), "r4-black", faces=without(DIRS, "south"),
          north=("cab-marquee-" + g, (0, 0, 12, 5), 230)),
        B("Top", (2, 25.2, 4.6), (14, 29.4, 15), art, faces=without(DIRS, "north")),
        B("Lid", (1.2, 29.4, 3.0), (14.8, 30.0, 15.5), "r4-blackmetal"),
        B("Shaft", (4.6, 14.0, 2.6), (5.2, 16.0, 3.2), "r4-chrome", faces=without(DIRS, "down", "up")),
        B("Ball", (4.15, 16.0, 2.15), (5.65, 17.5, 3.65), "cab-red"),
        B("Back", (2, 0.3, 15), (14, 29.4, 15.4), "r4-blackmetal", faces=("south",)),
    ]
    for k, (x, c) in enumerate(((8.0, "cab-red"), (9.8, "cab-yellow"), (11.6, "cab-red"))):
        els.append(B(f"Btn{k}", (x - 0.6, 14.0, 2.4), (x + 0.6, 14.6, 3.6), c, faces=without(DIRS, "down")))
    # The side panels: wider than the body, in the classic profile (kick, a step out round the panel, the screen's
    # slope, the marquee), each with its T-moulding along the front edge
    for sx, (xa, xb) in (("L", (1.4, 2.0)), ("R", (14.0, 14.6))):
        prof = [(0, 12.2, 3.3), (12.2, 15.0, 0.4), (15.0, 25.2, 4.0), (25.2, 29.4, 3.3)]
        for i, (y1, y2, z1) in enumerate(prof):
            els.append(B(f"Side{sx}{i}", (xa, y1, z1), (xb, y2, 15.4), art))
            els.append(B(f"Trim{sx}{i}", (xa - 0.05, y1, z1 - 0.3), (xb + 0.05, y2, z1), acc, glow=60, faces=without(DIRS, "south")))
    return shape("l31-retrocab-" + g, els)


def pinball_textures():
    # The playfield seen from above (front of the machine at the bottom of the picture)
    W = 32
    img = Image.new("RGBA", (W, W), rgba((18, 30, 90)))
    d = ImageDraw.Draw(img)
    for y in range(W):
        d.line([(0, y), (W - 1, y)], fill=rgba((18 + y, 30 + y // 2, 90 + y)))
    d.ellipse([3, 4, 11, 12], fill=rgba((240, 60, 140)))
    d.ellipse([18, 3, 26, 11], fill=rgba((60, 220, 240)))
    d.ellipse([11, 11, 19, 19], fill=rgba((250, 210, 50)))
    for c in ((5, 6), (20, 5), (13, 13)):
        d.ellipse([c[0], c[1], c[0] + 4, c[1] + 4], fill=rgba((255, 255, 255)))
    d.line([(2, 20), (11, 27)], fill=rgba((250, 250, 250)), width=2)  # the flippers
    d.line([(29, 20), (20, 27)], fill=rgba((250, 250, 250)), width=2)
    d.line([(1, 2), (1, 30)], fill=rgba((200, 200, 210)))
    d.line([(28, 6), (28, 30)], fill=rgba((200, 200, 210)))
    d.ellipse([15, 22, 17, 24], fill=rgba((230, 230, 236)))  # the ball
    save_tex(img, "r4-playfield")
    # The backglass: STARDUST over a skater under a star, the score display under it
    P = 64
    bg = Image.new("RGBA", (P, P), rgba((10, 8, 40)))
    d = ImageDraw.Draw(bg)
    for y in range(P):
        d.line([(0, y), (P - 1, y)], fill=rgba((10 + y // 2, 8, 40 + y)))
    star = [(32 + 14 * math.cos(math.radians(a)) * (1 if i % 2 == 0 else 0.42), 24 + 14 * math.sin(math.radians(a)) * (1 if i % 2 == 0 else 0.42))
            for i, a in enumerate(range(-90, 270, 36))]
    d.polygon(star, fill=rgba((255, 220, 60)))
    d.ellipse([28, 18, 36, 26], fill=rgba((255, 120, 200)))
    ctext(bg, 32, 3, "STARDUST", (255, 255, 255), sx=2)
    d.rectangle([6, 44, 57, 56], fill=rgba((20, 6, 0)))
    ctext(bg, 32, 47, "1250000", (255, 140, 30), sx=1)
    d.rectangle([2, 2, P - 3, P - 3], outline=rgba((255, 90, 200)))
    save_tex(bg, "r4-backglass")
    save_tex(M.painted_metal(seed=4220, base=(40, 20, 90), panel=False, chips=2, under=(90, 90, 96)), "r4-pincab")


def pinball():
    """A pinball machine: four legs with levellers, the cabinet sloping up to the back, the playfield under its lock-
    down bar, flipper buttons, the plunger, a coin door, and the lit backglass head on its neck at the back."""
    els = []
    for k, (x, z) in enumerate(((2.2, 1.4), (13.0, 1.4), (2.2, 13.2), (13.0, 13.2))):
        els += [B(f"Leg{k}", (x, 0.4, z), (x + 0.8, 9.2, z + 0.8), "r4-chrome", faces=without(DIRS, "up", "down")),
                B(f"Foot{k}", (x - 0.2, 0, z - 0.2), (x + 1.0, 0.4, z + 1.0), "r4-black")]
    tilt = (-5, 0, 0)
    o = (8, 9, 1)
    els += [
        B("Cab", (2, 9, 1), (14, 13, 15.6), "r4-pincab", rot=tilt, origin=o, up=("r4-playfield", FULL, 120)),
        B("RailL", (1.8, 13, 1), (2.6, 13.6, 15.6), "r4-chrome", rot=tilt, origin=o),
        B("RailR", (13.4, 13, 1), (14.2, 13.6, 15.6), "r4-chrome", rot=tilt, origin=o),
        B("Lockdown", (1.8, 12.6, 0.4), (14.2, 13.6, 1.4), "r4-chrome", rot=tilt, origin=o),
        B("Door", (5.0, 9.6, 0.7), (11.0, 12.4, 1.0), "r4-black", rot=tilt, origin=o, faces=without(DIRS, "south"),
          north=("cab-coin", (2.0, 4.0, 10.0, 10.0))),
        B("FlipL", (1.6, 11.0, 2.0), (2.0, 12.0, 3.0), "cab-red", rot=tilt, origin=o, faces=without(DIRS, "east")),
        B("FlipR", (14.0, 11.0, 2.0), (14.4, 12.0, 3.0), "cab-red", rot=tilt, origin=o, faces=without(DIRS, "west")),
        B("Plunger", (12.2, 10.6, 0.0), (12.8, 11.2, 1.0), "r4-chrome", rot=tilt, origin=o),
        B("PlungerKnob", (12.0, 10.4, -0.6), (13.0, 11.4, 0.0), "r4-black", rot=tilt, origin=o),
        B("Neck", (6.0, 13.5, 13.8), (10.0, 15.5, 15.4), "r4-pincab"),
        B("Head", (2.2, 15.5, 12.8), (13.8, 28.5, 16.0), "r4-pincab", north=("r4-backglass", FULL, 200)),
        B("HeadTrim", (2.0, 28.5, 12.6), (14.0, 29.0, 16.0), "r4-chrome"),
        B("HeadFrameL", (2.0, 15.5, 12.6), (2.4, 28.5, 12.8), "r4-chrome", faces=without(DIRS, "south")),
        B("HeadFrameR", (13.6, 15.5, 12.6), (14.0, 28.5, 12.8), "r4-chrome", faces=without(DIRS, "south")),
    ]
    return shape("l31-pinball", els)


def photobooth():
    """The photo booth: a blue cabinet, the curtain hung in folds from a chrome rod over the left half, the lit PHOTOS
    header standing proud, the right panel with sample strips, a coin box and the print slot, a stool and the camera
    window inside."""
    body = "booth-body"
    els = [
        B("Back", (0, 0, 14.6), (16, 30, 16), body),
        B("SideL", (0, 0, 1.0), (1.0, 30, 14.6), body),
        B("SideR", (15, 0, 1.0), (16, 30, 14.6), body),
        B("Roof", (0, 30, 0.6), (16, 31, 16), body),
        B("Kick", (0, 0, 0.6), (16, 1.0, 1.0), "r4-blackmetal", faces=without(DIRS, "south")),
        B("Head", (-0.2, 25.4, -0.4), (16.2, 30.0, 1.4), "r4-black", north=("booth-head", None, 230)),
        B("HeadTrim", (-0.3, 25.0, -0.5), (16.3, 25.4, 1.5), "r4-chrome"),
        B("Pillar", (9.0, 1.0, 0.6), (9.8, 25.0, 1.4), body),
        B("PanelR", (9.8, 1.0, 0.8), (15.0, 25.0, 1.4), body, north=("booth-strip", (0, 0, 16, 16))),
        B("Coin", (11.2, 13.0, 0.3), (13.6, 15.4, 0.8), "r4-chrome", faces=without(DIRS, "south")),
        B("CoinSlot", (12.0, 14.0, 0.25), (12.8, 14.8, 0.3), "r4-black", faces=("north",)),
        B("Print", (10.6, 5.0, 0.4), (14.2, 6.4, 0.8), "r4-chrome", faces=without(DIRS, "south")),
        B("PrintSlot", (11.0, 5.4, 0.35), (13.8, 5.8, 0.4), "r4-black", faces=("north",)),
        B("Rod", (0.8, 24.2, 1.1), (9.2, 24.7, 1.6), "r4-chrome"),
        B("Stool", (3.0, 6.0, 7.0), (8.0, 7.0, 12.0), "r4-black"),
        B("StoolPost", (5.2, 0, 9.2), (5.8, 6.0, 9.8), "r4-chrome", faces=without(DIRS, "up", "down")),
        B("Camera", (3.5, 13.5, 14.4), (7.5, 17.0, 14.6), "r4-black", faces=("north",), north=("r4-led-cyan", None, 90)),
        B("Mirror", (2.0, 17.5, 14.4), (9.0, 22.0, 14.6), "mirror", faces=("north",)),
    ]
    # The curtain: four folds stepping in and out under the rod
    for k in range(5):
        x1 = 1.0 + k * 1.6
        z = 1.3 if k % 2 == 0 else 2.0
        els.append(B(f"Fold{k}", (x1, 2.0 + (k % 2) * 0.4, z), (x1 + 1.6, 24.2, z + 0.6), "booth-curtain",
                     faces=without(DIRS, "south")))
    return shape("l31-photobooth", els)


def dispenser():
    """The green-card machine: a cabinet on a plinth, the lit GREEN CARDS header, a bill acceptor, a big button and the
    card tray."""
    save_tex(M.painted_metal(seed=4230, base=(96, 40, 150), panel=False, chips=2), "r4-disp")
    head = Image.new("RGBA", (S, S), rgba((20, 140, 60)))
    ctext(head, 16, 6, "GREEN", (255, 255, 255))
    ctext(head, 16, 14, "CARDS", (255, 255, 255))
    save_tex(head, "r4-disphead")
    els = [
        B("Plinth", (3, 0, 4.6), (13, 1.2, 11.4), "r4-black"),
        B("Body", (3.4, 1.2, 5.0), (12.6, 22, 11.0), "r4-disp"),
        B("Head", (3.0, 22, 4.4), (13.0, 27, 11.4), "r4-black", north=("r4-disphead", FULL, 210)),
        B("Bill", (5.0, 15.0, 4.4), (11.0, 17.4, 5.0), "r4-black", faces=without(DIRS, "south")),
        B("BillLip", (5.4, 15.6, 4.2), (10.6, 16.0, 4.4), "r4-led-cyan", glow=180, faces=("north", "up", "down")),
        B("Button", (6.4, 10.4, 4.3), (9.6, 13.6, 5.0), "r4-led-cyan", glow=200, faces=without(DIRS, "south")),
        B("ButtonRing", (6.0, 10.0, 4.6), (10.0, 14.0, 5.0), "r4-chrome", faces=without(DIRS, "south")),
        B("Tray", (5.4, 4.0, 3.6), (10.6, 5.0, 5.0), "r4-chrome"),
        B("TrayBack", (5.4, 5.0, 4.6), (10.6, 7.6, 5.0), "r4-black", faces=without(DIRS, "south")),
        B("Card", (6.4, 5.0, 3.8), (9.6, 5.2, 4.8), "cab-yellow", faces=("up", "north")),
    ]
    return shape("l31-dispenser", els)


# ======================================================================== The snack bar

def slushie():
    """A slushie machine on its stainless cabinet: two bowls of frozen drink (blue raspberry and cherry) turning on their
    augers under lit lids, taps and a drip tray, the menu header; 31 units tall."""
    steel = M.brushed_metal(seed=4240, base=(176, 180, 186), sheen=12, direction="v")
    save_tex(M.grime(steel, 0.10, 4241, color=(90, 86, 80), bias="bottom"), "r4-steel")
    for n, c in (("blue", (40, 110, 230)), ("red", (220, 30, 60))):
        img = M.noise_hv(c, 6, 4242 + len(n), S, 8, (4, 4))
        px = img.load()
        for y in range(S):
            for x in range(S):
                r, g, b, a = px[x, y]
                k = 1.35 if x in (4, 5) else 1.0  # the bowl's highlight
                if y < 4:
                    k *= 0.75  # air under the lid
                px[x, y] = (M.clamp(r * k + (40 if x in (4, 5) else 0)), M.clamp(g * k + (40 if x in (4, 5) else 0)),
                            M.clamp(b * k + (40 if x in (4, 5) else 0)), 255)
        save_tex(img, "r4-slush-" + n)
    head = Image.new("RGBA", (S, S), rgba((240, 240, 246)))
    d = ImageDraw.Draw(head)
    d.rectangle([0, 10, 31, 22], fill=rgba((30, 90, 220)))
    ctext(head, 16, 14, "SLUSH", (255, 255, 255))
    save_tex(head, "r4-slushhead")
    els = [
        B("Cabinet", (0.5, 0, 1.5), (15.5, 14, 15.5), "r4-steel"),
        B("Kick", (0.7, 0, 1.2), (15.3, 1.0, 1.5), "r4-black", faces=without(DIRS, "south")),
        B("DoorSeam", (7.9, 1.2, 1.4), (8.1, 13.6, 1.5), "r4-black", faces=("north",)),
        B("HandleL", (6.6, 6, 1.0), (7.2, 10, 1.5), "r4-chrome"),
        B("HandleR", (8.8, 6, 1.0), (9.4, 10, 1.5), "r4-chrome"),
        B("Worktop", (0, 14, 1.0), (16, 15, 16), "r4-steel"),
        B("Base", (1.5, 15, 3.0), (14.5, 19, 14.0), "r4-steel"),
        B("Drip", (2.0, 15, 1.6), (14.0, 15.6, 3.0), "r4-grille"),
        B("Back", (1.5, 19, 11.5), (14.5, 30, 14.0), "r4-steel"),
        B("Head", (1.2, 28, 2.4), (14.8, 31, 14.2), "r4-black", north=("r4-slushhead", FULL, 200), up=("r4-steel", None)),
    ]
    for k, (x1, x2, n) in enumerate(((2.0, 7.6, "blue"), (8.4, 14.0, "red"))):
        els += [
            B(f"Bowl{k}", (x1, 19, 3.2), (x2, 28, 11.5), "r4-slush-" + n, glow=60),
            B(f"Tap{k}", ((x1 + x2) / 2 - 0.8, 17.2, 2.2), ((x1 + x2) / 2 + 0.8, 19.0, 3.2), "r4-black"),
            B(f"Lever{k}", ((x1 + x2) / 2 - 0.3, 18.6, 1.6), ((x1 + x2) / 2 + 0.3, 21.0, 2.2), "r4-chrome"),
        ]
    return shape("l31-slushie", els)


# ======================================================================== The cinema

def cinemabench():
    """A segment of the lore's continuous steel bench: a perforated seat pan with a rolled front, a back on a slant,
    a T-leg bolted to its foot plate, and a cup holder on the back for the row behind."""
    perf = M.brushed_metal(seed=4250, base=(96, 102, 114), sheen=10)
    pp = perf.load()
    for y in range(2, S, 4):
        for x in range(2 + (y // 4) % 2 * 2, S, 4):
            pp[x, y] = (20, 22, 28, 255)
    save_tex(perf, "r4-perf")
    gun = M.painted_metal(seed=4251, base=(58, 62, 72), panel=False, chips=3, under=(140, 140, 146))
    save_tex(gun, "r4-gunmetal")
    disc_tex("r4-holder", 16, lambda d, x, y: (16, 16, 18) if d < 0.7 else (70, 74, 84))
    els = [
        B("Seat", (0, 6.2, 3.4), (16, 7.0, 11.4), "r4-gunmetal", up=("r4-perf", None)),
        B("Roll", (0, 5.6, 2.8), (16, 6.9, 3.6), "r4-gunmetal", faces=without(DIRS, "east", "west")),
        B("Back", (0, 7.6, 11.0), (16, 14.0, 11.8), "r4-gunmetal", rot=(10, 0, 0), origin=(8, 7.6, 11.4),
          north=("r4-perf", None), faces=without(DIRS, "east", "west")),
        B("BackRail", (0, 13.6, 11.2), (16, 14.6, 12.4), "r4-chrome", rot=(10, 0, 0), origin=(8, 7.6, 11.4),
          faces=without(DIRS, "east", "west")),
        B("Post", (7.4, 0.6, 6.6), (8.6, 6.2, 7.8), "r4-gunmetal", faces=without(DIRS, "up", "down")),
        B("Arm", (7.5, 5.4, 3.8), (8.5, 6.2, 11.6), "r4-gunmetal", faces=without(DIRS, "up")),
        B("Strut", (7.5, 6.2, 10.4), (8.5, 8.4, 11.2), "r4-gunmetal", faces=without(DIRS, "up", "down")),
        B("Foot", (5.6, 0, 4.6), (10.4, 0.6, 9.8), "r4-blackmetal", faces=without(DIRS, "down")),
        B("BoltA", (6.0, 0.6, 5.0), (6.6, 0.9, 5.6), "r4-chrome", faces=without(DIRS, "down")),
        B("BoltB", (9.4, 0.6, 8.8), (10.0, 0.9, 9.4), "r4-chrome", faces=without(DIRS, "down")),
        B("Holder", (6.6, 9.4, 12.6), (9.4, 10.2, 15.0), "r4-gunmetal", up=("r4-holder", FULL)),
        B("HolderArm", (7.6, 8.4, 11.6), (8.4, 9.4, 13.2), "r4-gunmetal", faces=without(DIRS, "up")),
    ]
    return shape("l31-cinemabench", els)


def mediacab():
    """The cinema TV's low cabinet: walnut veneer with two doors and pulls, an open shelf with a VCR and a disc player
    (lit clocks), on a black plinth; the sound bar on top with its grille and a blue standby light."""
    save_tex(M.wood_planks(seed=4260, base=(92, 60, 40), planks=1, direction="h", grain=4, flecks=0.4), "r4-walnut")
    vcr = Image.new("RGBA", (S, S), rgba((30, 30, 34)))
    d = ImageDraw.Draw(vcr)
    d.rectangle([3, 3, 18, 7], fill=rgba((12, 12, 14)))  # the tape door
    d.rectangle([21, 3, 29, 7], fill=rgba((8, 20, 14)))
    d.rectangle([22, 4, 28, 6], fill=rgba((60, 255, 140)))  # 12:00, blinking forever
    for k in range(4):
        d.rectangle([4 + k * 4, 10, 6 + k * 4, 11], fill=rgba((140, 140, 150)))
    save_tex(vcr, "r4-vcr")
    els = [
        B("Plinth", (0.4, 0, 4.4), (15.6, 0.8, 14.6), "r4-black", faces=without(DIRS, "down")),
        B("Carcass", (0, 0.8, 4.0), (16, 7.6, 15.0), "r4-walnut"),
        B("DoorL", (0.6, 1.4, 3.7), (5.6, 7.0, 4.0), "r4-walnut", faces=without(DIRS, "south")),
        B("DoorR", (10.4, 1.4, 3.7), (15.4, 7.0, 4.0), "r4-walnut", faces=without(DIRS, "south")),
        B("PullL", (4.6, 3.8, 3.4), (5.0, 5.0, 3.7), "r4-chrome", faces=without(DIRS, "south")),
        B("PullR", (11.0, 3.8, 3.4), (11.4, 5.0, 3.7), "r4-chrome", faces=without(DIRS, "south")),
        B("Shelf", (5.9, 1.2, 3.9), (10.1, 7.2, 4.05), "r4-black", faces=("north",)),
        B("Vcr", (6.1, 4.4, 3.6), (9.9, 5.6, 4.0), "r4-black", faces=without(DIRS, "south"), north=("r4-vcr", (0, 0, 16, 7))),
        B("Disc", (6.1, 2.0, 3.6), (9.9, 3.0, 4.0), "r4-black", faces=without(DIRS, "south"), north=("r4-cdtop", (0, 0, 16, 6))),
        B("Bar", (1.0, 7.6, 8.4), (15.0, 9.6, 12.6), "r4-black"),
        B("BarGrille", (1.2, 7.8, 8.2), (14.8, 9.4, 8.4), "r4-grille", faces=("north",)),
        B("Standby", (13.6, 8.0, 8.1), (14.0, 8.4, 8.2), "r4-led-cyan", glow=255, faces=("north",)),
    ]
    return shape("l31-mediacab", els)


def riser():
    """A cinema step (round 3's block, its shape rebuilt): carpet on top, an aluminium nosing round its edge and a row of
    amber aisle lights under it on every side (where a neighbouring step stands, they are inside it and unseen)."""
    els = [B("Step", (0, 0, 0), (16, 16, 16), "riser-side", up=("riser-carpet", None), down=("riser-carpet", None))]
    side = [B("Nose", (-0.08, 15.0, -0.08), (16.08, 15.96, 0.0), "r4-alu", faces=without(DIRS, "south"))]
    for k, x in enumerate((2.5, 8.0, 13.5)):
        side.append(B(f"Led{k}", (x - 0.6, 13.7, -0.1), (x + 0.6, 14.3, 0.0), "r4-led-amber", glow=255, faces=without(DIRS, "south")))
    for t in range(4):
        for e in turn(side, t):
            e["name"] = e["name"] + str(t)
            els.append(e)
    return shape("l31-riser", els)


def table():
    """The food court's cafe table: white laminate with a magenta edge band, on a chrome column and a cross foot with
    levellers; a napkin holder, salt and pepper and a ketchup bottle on it. Not oriented."""
    disc_tex("r4-napkin", 16, lambda d, x, y: (250, 250, 246))
    els = [
        B("Top", (1, 11.2, 1), (15, 12.0, 15), "table-laminate", faces=("up", "down")),
        B("Edge", (0.8, 10.9, 0.8), (15.2, 12.0, 15.2), "r4-padpink", faces=("north", "east", "south", "west", "down")),
        B("Column", (7.2, 1.0, 7.2), (8.8, 10.9, 8.8), "r4-chrome", faces=without(DIRS, "up", "down")),
        B("Spider", (5.0, 10.2, 7.4), (11.0, 10.9, 8.6), "r4-chrome", faces=without(DIRS, "up")),
        B("SpiderZ", (7.4, 10.25, 5.0), (8.6, 10.85, 11.0), "r4-chrome", faces=without(DIRS, "up")),
        B("FootX", (2.0, 0.4, 7.2), (14.0, 1.0, 8.8), "r4-chrome"),
        B("FootZ", (7.2, 0.45, 2.0), (8.8, 0.95, 14.0), "r4-chrome", faces=("north", "south", "east", "west")),
        B("Napkins", (6.0, 12.0, 7.0), (10.0, 14.6, 9.0), "plate-white"),
        B("Holder", (5.7, 12.0, 6.7), (10.3, 12.8, 9.3), "r4-chrome"),
        B("Salt", (11.0, 12.0, 7.4), (11.8, 13.6, 8.2), "plate-white"),
        B("Pepper", (11.0, 12.0, 8.6), (11.8, 13.6, 9.4), "r4-black"),
        B("Ketchup", (4.0, 12.0, 7.6), (5.0, 14.6, 8.6), "cab-red"),
        B("KetchupCap", (4.2, 14.6, 7.8), (4.8, 15.2, 8.4), "plate-white"),
    ]
    for k, (x, z) in enumerate(((1.6, 7.4), (13.6, 7.4), (7.4, 1.6), (7.4, 13.6))):
        els.append(B(f"Lev{k}", (x, 0, z), (x + 1.2, 0.4, z + 1.2), "r4-black", faces=without(DIRS, "down")))
    return shape("l31-table", els)


# ======================================================================== Neon tubes and the big TV's bezel

NEON_PLATES = ("name", "arc", "arcbig", "prizes", "snackbig")


def neon_tubes():
    """The neon wall mounts get their tubes: a cut-out of the picture's bright strokes, lit, standing a unit and a half
    proud of the backing board (round 3's flat plate stays as the board with its halo), on chrome stand-offs; the big
    TV's panels get a bezel round the screen's outer edge, a unit deep."""
    import json
    from gen_31 import SHAPES
    for path in sorted(os.listdir(SHAPES)):
        m = path[len("l31-plate-"):-len(".json")] if path.startswith("l31-plate-") else None
        if not m:
            continue
        name = m.rstrip("0123456789")
        if name not in NEON_PLATES and name != "bigtv":
            continue
        full = os.path.join(SHAPES, path)
        with open(full, encoding="utf-8") as f:
            data = json.load(f)
        els = [e for e in data["elements"] if not e["name"].startswith("R4")]
        panel = els[0]
        (x1, y1, z1), (x2, y2, z2) = panel["from"], panel["to"]
        if name == "bigtv":
            col, row = int(m[-2]), int(m[-1])
            bz = (13.8, 15.0)
            if row == 0:
                els.append(B("R4BezelT", (x1, y2 - 1.0, bz[0]), (x2, y2, bz[1]), "r4-black", faces=without(DIRS, "south")))
            if row == 2:
                els.append(B("R4BezelB", (x1, y1, bz[0]), (x2, y1 + 1.2, bz[1]), "r4-black", faces=without(DIRS, "south")))
                if col == 2:
                    els.append(B("R4Logo", (7.0, y1 + 0.3, bz[0] - 0.05), (9.0, y1 + 0.8, bz[0]), "r4-chrome", faces=("north",)))
            if col == 0:
                els.append(B("R4BezelL", (x2 - 1.0, y1, bz[0]), (x2, y2, bz[1]), "r4-black", faces=without(DIRS, "south")))
            if col == 4:
                els.append(B("R4BezelR", (x1, y1, bz[0]), (x1 + 1.0, y2, bz[1]), "r4-black", faces=without(DIRS, "south")))
        else:
            # The tube layer: the picture's strokes only (bright, saturated pixels), everything else clear
            src = Image.open(os.path.join(TEX, f"plate-{m}.png")).convert("RGBA")
            tube = Image.new("RGBA", src.size, (0, 0, 0, 0))
            sp, tp = src.load(), tube.load()
            for y in range(src.size[1]):
                for x in range(src.size[0]):
                    r, g, b, a = sp[x, y]
                    if a > 0 and max(r, g, b) > 200:
                        tp[x, y] = (min(255, r + 30), min(255, g + 30), min(255, b + 30), 255)
            save_tex(tube, f"r4-tube-{m}")
            uv = panel["faces"]["north"]["uv"]
            t = B("R4Tubes", (x1, y1, z1 - 1.6), (x2, y2, z1 - 1.4), "r4-black", faces=("north",), north=(f"r4-tube-{m}", uv, 255))
            els.append(t)
            data["textures"][f"r4-tube-{m}"] = f"backrooms:block/31/r4-tube-{m}"
            for k, sx in enumerate((x1 + 1.5, x2 - 2.0)):
                if x2 - x1 > 6:
                    els.append(B(f"R4Standoff{k}", (sx, (y1 + y2) / 2 - 0.25, z1 - 1.4), (sx + 0.5, (y1 + y2) / 2 + 0.25, z1), "r4-chrome",
                                 faces=without(DIRS, "north", "south")))
        data["elements"] = els
        for e in els:
            for fc in e["faces"].values():
                k = fc["texture"][1:]
                if k not in data["textures"]:
                    data["textures"][k] = "backrooms:block/31/" + k
        write_json(full, data)


# ======================================================================== Restrooms

def stall():
    """A toilet stall: laminate partitions on chrome feet with a head rail, the door ajar on three hinges with its
    VACANT indicator and coat hook, the toilet with lid, seat, cistern and flush, a paper holder."""
    lam = M.painted_metal(seed=4270, base=(150, 186, 200), panel=False, chips=2, under=(200, 200, 200))
    save_tex(M.grime(lam, 0.10, 4271, color=(100, 110, 110), bias="bottom"), "r4-laminate")
    vac = Image.new("RGBA", (S, S), rgba((240, 240, 240)))
    dv = ImageDraw.Draw(vac)
    dv.rectangle([0, 16, 31, 31], fill=rgba((40, 170, 70)))
    save_tex(vac, "r4-vacant")
    door_rot = (0, -28, 0)
    o = (1.0, 14, 0.85)
    els = [
        B("PartL", (0, 2, 0.5), (0.8, 28, 16), "r4-laminate"),
        B("PartR", (15.2, 2, 0.5), (16, 28, 16), "r4-laminate"),
        B("FootL", (0.05, 0, 1.0), (0.75, 2, 1.7), "r4-chrome"),
        B("FootR", (15.25, 0, 1.0), (15.95, 2, 1.7), "r4-chrome"),
        B("FootLb", (0.05, 0, 14.0), (0.75, 2, 14.7), "r4-chrome"),
        B("FootRb", (15.25, 0, 14.0), (15.95, 2, 14.7), "r4-chrome"),
        B("Rail", (0, 27.2, 0.3), (16, 28.2, 1.1), "r4-chrome"),
        B("Door", (1.0, 2.5, 0.5), (14.6, 27, 1.2), "r4-laminate", rot=door_rot, origin=o),
        B("Lock", (12.6, 13.0, 0.0), (13.8, 14.6, 0.5), "r4-chrome", rot=door_rot, origin=o, north=("r4-vacant", FULL)),
        B("Hook", (7.4, 22.0, 1.2), (8.6, 23.0, 2.2), "r4-chrome", rot=door_rot, origin=o),
        B("Bowl", (5.2, 0, 7.4), (10.8, 6.0, 13.5), "porcelain"),
        B("BowlFront", (5.8, 0.5, 6.6), (10.2, 5.8, 7.4), "porcelain"),
        B("Seat", (4.8, 6.0, 6.6), (11.2, 6.7, 13.6), "plate-white"),
        B("Lid", (5.0, 6.7, 12.8), (11.0, 13.0, 13.5), "plate-white", rot=(-8, 0, 0), origin=(8, 6.7, 13.2)),
        B("Tank", (4.4, 6.5, 13.6), (11.6, 12.5, 15.8), "porcelain"),
        B("TankLid", (4.2, 12.5, 13.4), (11.8, 13.1, 16.0), "porcelain"),
        B("Flush", (10.2, 11.2, 13.2), (11.2, 11.8, 13.6), "r4-chrome"),
        B("Roll", (13.4, 9, 9), (15.2, 10.8, 10.8), "plate-white"),
        B("RollArm", (15.0, 9.6, 9.6), (15.2, 10.2, 10.2), "r4-chrome"),
    ]
    for k, y in enumerate((4.5, 14.0, 23.5)):
        els.append(B(f"Hinge{k}", (0.6, y, 0.3), (1.4, y + 1.5, 1.4), "r4-chrome"))
    return shape("l31-stall", els)


def vanity():
    """A washroom vanity: a solid-surface top on a laminate cabinet with doors, the basin set in it with an overflow,
    a mixer tap with its lever, a soap pump, and a splashback."""
    els = [
        B("Plinth", (0.4, 0, 3.6), (15.6, 0.8, 16), "r4-black", faces=without(DIRS, "down")),
        B("Cabinet", (0, 0.8, 3.2), (16, 11, 16), "vanity-front"),
        B("DoorSeam", (7.9, 1.4, 3.1), (8.1, 10.4, 3.2), "r4-black", faces=("north",)),
        B("PullL", (6.6, 8.0, 2.8), (7.2, 9.6, 3.2), "r4-chrome"),
        B("PullR", (8.8, 8.0, 2.8), (9.4, 9.6, 3.2), "r4-chrome"),
        B("Top", (0, 11, 2.0), (16, 12.5, 16), "vanity-top"),
        B("Basin", (3.6, 10.0, 4.2), (12.4, 12.6, 12.4), "porcelain", faces=without(DIRS, "up")),
        B("Bowl", (4.4, 12.5, 5.0), (11.6, 12.6, 11.6), "porcelain", faces=("up",)),
        B("Well", (5.4, 12.6, 6.0), (10.6, 12.62, 10.6), "plate-black", faces=("up",)),
        B("Drain", (7.6, 12.62, 7.8), (8.4, 12.64, 8.6), "r4-chrome", faces=("up",)),
        B("TapPost", (7.4, 12.5, 12.6), (8.6, 16.0, 13.8), "r4-chrome"),
        B("Spout", (7.6, 15.0, 9.6), (8.4, 15.8, 12.6), "r4-chrome"),
        B("Lever", (7.7, 16.0, 12.2), (8.3, 16.6, 14.6), "r4-chrome"),
        B("Soap", (12.6, 12.5, 12.6), (14.4, 15.4, 14.4), "plate-white"),
        B("Pump", (13.2, 15.4, 12.8), (13.8, 16.4, 14.2), "r4-black"),
        B("Splash", (0, 12.5, 15.2), (16, 18.0, 16), "porcelain"),
    ]
    return shape("l31-vanity", els)


def dryer():
    """A wall hand dryer: a rounded white body (stepped to read round), the chrome nozzle turned down, the push button
    and its PUSH plate (an l31-plate fitting: rewritten here)."""
    import json
    from gen_31 import SHAPES
    els = [B("Back", (3.2, 5.6, 15.2), (12.8, 13.6, 16), "plate-white"),
           B("Body", (3.6, 6.0, 10.6), (12.4, 13.2, 15.2), "plate-white"),
           B("BodyX", (4.4, 5.4, 11.2), (11.6, 13.8, 15.2), "plate-white", faces=without(DIRS, "south")),
           B("Front", (4.4, 6.6, 10.0), (11.6, 12.6, 10.6), "plate-white", faces=without(DIRS, "south")),
           B("Nozzle", (6.6, 4.4, 11.2), (9.4, 5.4, 14.0), "r4-chrome"),
           B("NozzleMouth", (6.8, 4.35, 11.4), (9.2, 4.4, 13.8), "r4-black", faces=("down",)),
           B("Button", (7.2, 8.6, 9.6), (8.8, 10.2, 10.0), "r4-chrome", faces=without(DIRS, "south")),
           B("Badge", (6.4, 11.0, 9.95), (9.6, 11.8, 10.0), "r4-black", faces=("north",))]
    data = {"textureWidth": 16, "textureHeight": 16,
            "textures": {k: "backrooms:block/31/" + k for k in sorted({f["texture"][1:] for e in els for f in e["faces"].values()})},
            "elements": els}
    write_json(os.path.join(SHAPES, "l31-plate-dryer00.json"), data)


# ======================================================================== The snack bar's popcorn machine, the jukebox

def popcorn():
    """A kettle popcorn machine on its cart (similar to Level Fun's cart, the rink's own): a red cabinet on casters, the
    case framed in chrome with the popcorn heaped inside and the kettle hung from its roof, the lit POPCORN header and a
    scoop; 30 units tall."""
    red = M.painted_metal(seed=4280, base=(196, 30, 36), panel=False, chips=4, under=(220, 220, 220))
    save_tex(M.grime(red, 0.10, 4281, color=(60, 20, 20), bias="bottom"), "r4-red")
    pop = Image.new("RGBA", (S, S), rgba((250, 236, 170)))
    rng = random.Random(4282)
    d = ImageDraw.Draw(pop)
    for _ in range(90):
        x, y, r = rng.randrange(S), rng.randrange(S), rng.randint(1, 2)
        c = rng.choice(((255, 250, 220), (246, 222, 140), (230, 196, 100), (255, 255, 240)))
        d.ellipse([x - r, y - r, x + r, y + r], fill=rgba(c))
    save_tex(pop, "r4-popcorn")
    head = Image.new("RGBA", (S, S), rgba((196, 30, 36)))
    d = ImageDraw.Draw(head)
    d.rectangle([1, 9, 30, 22], fill=rgba((255, 236, 120)))
    ctext(head, 16, 13, "POPCORN", (180, 20, 30))
    save_tex(head, "r4-pophead")
    els = [
        B("Cart", (1.0, 2.0, 2.0), (15.0, 12.0, 14.0), "r4-red"),
        B("CartTop", (0.6, 12.0, 1.6), (15.4, 12.8, 14.4), "r4-chrome"),
        B("CartDoor", (3.0, 3.5, 1.7), (13.0, 10.5, 2.0), "r4-red", faces=without(DIRS, "south")),
        B("CartPull", (11.6, 6.2, 1.3), (12.2, 8.0, 1.7), "r4-chrome"),
        B("Shelf", (1.4, 4.0, 1.8), (14.6, 4.4, 14.2), "r4-chrome", faces=("up",)),
        B("Floor", (2.0, 12.8, 2.6), (14.0, 13.4, 13.4), "r4-steel", faces=("up",)),
        B("Heap", (2.4, 12.8, 3.0), (13.6, 16.6, 13.0), "r4-popcorn"),
        B("HeapTop", (4.0, 16.6, 4.6), (12.0, 18.0, 11.4), "r4-popcorn", faces=without(DIRS, "down")),
        B("Kettle", (5.6, 21.2, 6.0), (10.4, 24.0, 10.8), "r4-steel"),
        B("KettleRod", (7.7, 24.2, 8.1), (8.3, 26.4, 8.7), "r4-chrome", faces=without(DIRS, "up", "down")),
        B("KettleLip", (5.2, 23.6, 5.6), (10.8, 24.2, 11.2), "r4-chrome"),
        B("Roof", (1.0, 26.4, 2.0), (15.0, 27.2, 14.0), "r4-red"),
        B("Head", (0.6, 27.2, 1.6), (15.4, 30.4, 14.4), "r4-red", north=("r4-pophead", FULL, 200), south=("r4-pophead", FULL, 200)),
        B("Scoop", (11.0, 16.2, 3.6), (12.4, 17.0, 6.6), "r4-chrome", rot=(-20, 0, 0), origin=(11.7, 16.6, 5.0)),
    ]
    # The case's chrome frame (glass implied: open)
    for k, (x, z) in enumerate(((1.6, 2.2), (13.8, 2.2), (1.6, 13.2), (13.8, 13.2))):
        els.append(B(f"Post{k}", (x, 12.8, z), (x + 0.6, 26.4, z + 0.6), "r4-chrome", faces=without(DIRS, "up", "down")))
    els.append(B("RailF", (1.6, 15.6, 2.2), (14.4, 16.0, 2.6), "r4-chrome", faces=without(DIRS, "east", "west")))
    for k, (x, z) in enumerate(((2.0, 3.0), (13.0, 3.0), (2.0, 12.0), (13.0, 12.0))):
        els.append(B(f"Wheel{k}", (x, 0, z), (x + 1.0, 2.0, z + 1.0), "r4-black", east=("r4-wheel-red", FULL), west=("r4-wheel-red", FULL)))
    return shape("l31-popcorn", els)


def jukebox():
    """A 1990s jukebox: a wood cabinet under a stepped neon arch, the record window with the carousel behind it, the
    selector strip of buttons and title cards, bubble tubes up both sides, a chrome grille over the speaker; 22 units."""
    els = [
        B("Plinth", (1.0, 0, 4.0), (15.0, 1.2, 13.0), "r4-chrome"),
        B("Body", (1.4, 1.2, 4.6), (14.6, 15.0, 12.6), "juke-body"),
        B("Grille", (3.0, 2.2, 4.3), (13.0, 7.6, 4.6), "r4-grille", faces=without(DIRS, "south")),
        B("GrilleRim", (2.6, 1.8, 4.4), (13.4, 8.0, 4.5), "r4-chrome", faces=("north",)),
        B("Keys", (3.0, 8.4, 3.4), (13.0, 9.6, 4.6), "r4-chrome", rot=(-20, 0, 0), origin=(8, 9.0, 4.6), up=("r4-led-amber", None, 120)),
        B("Window", (3.0, 10.2, 4.3), (13.0, 14.6, 4.6), "r4-black", faces=without(DIRS, "south"), north=("juke-front", (1, 1, 15, 6), 160)),
        B("Arch1", (1.8, 15.0, 5.0), (14.2, 17.4, 12.2), "juke-body"),
        B("Arch2", (3.4, 17.4, 5.4), (12.6, 19.6, 11.8), "juke-body"),
        B("Arch3", (5.6, 19.6, 5.8), (10.4, 21.4, 11.4), "juke-body"),
        B("Dome", (6.6, 21.4, 6.4), (9.4, 22.2, 10.8), "r4-chrome"),
        B("Neon1", (1.6, 15.0, 4.6), (14.4, 15.6, 5.0), "juke-neoncyan", glow=255, faces=without(DIRS, "south")),
        B("Neon2", (3.2, 17.4, 5.0), (12.8, 18.0, 5.4), "juke-neonpink", glow=255, faces=without(DIRS, "south")),
        B("Neon3", (5.4, 19.6, 5.4), (10.6, 20.2, 5.8), "juke-neoncyan", glow=255, faces=without(DIRS, "south")),
    ]
    for k, x in enumerate((0.6, 14.4)):
        els += [B(f"Tube{k}", (x, 1.4, 5.2), (x + 1.0, 15.0, 6.2), "juke-neonpink", glow=255),
                B(f"TubeCap{k}", (x - 0.1, 15.0, 5.1), (x + 1.1, 15.6, 6.3), "r4-chrome")]
    return shape("l31-jukebox", els)


# ======================================================================== The rink's coin lockers

def locker_textures():
    for n, c in (("blue", (40, 96, 190)), ("orange", (232, 120, 30))):
        img = M.painted_metal(seed=4290 + len(n), base=c, panel=False, chips=4, under=(150, 150, 150))
        d = ImageDraw.Draw(img)
        for y in (4, 7, 10):
            d.rectangle([8, y, 23, y + 1], fill=rgba(tuple(int(v * 0.35) for v in c)))  # louvres
        M.grime(img, 0.12, 4293 + len(n), color=(40, 40, 46), bias="bottom", cover=0.4)
        save_tex(img, "r4-lockerdoor-" + n)
    body = M.painted_metal(seed=4295, base=(70, 72, 80), panel=False, chips=3, under=(140, 140, 140))
    save_tex(body, "r4-lockerbody")
    for k in range(8):
        img = Image.new("RGBA", (S, S), rgba((230, 226, 210)))
        ctext(img, 16, 4, str(101 + k * 7), (30, 30, 36), sx=2)
        save_tex(img, f"r4-lockernum{k}")
    tag = Image.new("RGBA", (S, S), rgba((240, 110, 30)))
    ctext(tag, 16, 12, "25", (255, 255, 255), sx=2)
    save_tex(tag, "r4-lockertag")


def locker(part):
    """One block of a bank of coin lockers set in the wall, its face north: two doors across and two high in it (four
    small lockers), each a door in its frame with louvres, a number plate, the coin lock with its key on an orange tag
    (the key gone and the door ajar on one); the lower block has the kick base. The block is a full cube: a wall."""
    els = [B("Body", (0, 0, 0.8), (16, 16, 16), "r4-lockerbody", north=("r4-black", None))]
    y0 = 1.6 if part == "lower" else 0.0
    if part == "lower":
        els.append(B("Kick", (0, 0, 0.4), (16, 1.6, 0.8), "r4-blackmetal", faces=without(DIRS, "south")))
    els.append(B("FrameTop", (0, 15.4, 0.3), (16, 16, 0.8), "r4-lockerbody", faces=without(DIRS, "south")))
    els.append(B("FrameMid", (7.7, y0, 0.3), (8.3, 15.4, 0.8), "r4-lockerbody", faces=without(DIRS, "south")))
    h = (15.4 - y0) / 2
    k = 0
    for row in range(2):
        ya = y0 + row * h + 0.3
        yb = ya + h - 0.6
        for col, (xa, xb) in enumerate(((0.4, 7.5), (8.5, 15.6))):
            colour = "orange" if (row + col + (part == "upper")) % 3 == 0 else "blue"
            ajar = part == "lower" and row == 1 and col == 0
            rot = (0, 35, 0) if ajar else None
            o = (xa, ya, 0.5)
            els += [
                B(f"Door{k}", (xa, ya, 0.3), (xb, yb, 0.6), "r4-lockerdoor-" + colour, rot=rot, origin=o,
                  north=("r4-lockerdoor-" + colour, FULL)),
                B(f"Num{k}", (xa + 2.0, yb - 1.4, 0.2), (xb - 2.0, yb - 0.6, 0.3), "r4-black", faces=("north",),
                  north=(f"r4-lockernum{(k + (4 if part == 'upper' else 0)) % 8}", (0, 0, 16, 8)), rot=rot, origin=o),
                B(f"Lock{k}", (xb - 2.2, ya + 1.6, 0.0), (xb - 0.8, ya + 3.4, 0.3), "r4-chrome", faces=without(DIRS, "south"), rot=rot, origin=o),
            ]
            if not ajar:
                els.append(B(f"Key{k}", (xb - 1.8, ya + 0.6, -0.3), (xb - 1.2, ya + 1.6, 0.0), "r4-lockertag", faces=without(DIRS, "south")))
            else:
                els.append(B(f"Dark{k}", (xa + 0.2, ya + 0.2, 0.75), (xb - 0.2, yb - 0.2, 0.8), "r4-black", faces=("north",)))
            k += 1
    return shape("l31-locker-" + part, els)


# ======================================================================== Block types

def blocks():
    materials()
    skate_textures()
    dj_textures()
    speaker_textures()
    ball_textures()
    rinkwood()
    discoball()

    ref = skateshelf()
    prop_block("l31-skateshelf", "Level 31: a rental cubby block of birch ply, two by three cubbies, a pair of quad skates heel-out in each (one rented out), size tags on the shelf edges; open toward the side",
               lambda k: ref, (0, 0, 0, 1, 1, 1), (0, 0, 0, 1, 1, 1), material="Wood", sounds=WOOD, resistance=3)

    shapes = {"straight": shape("l31-barrier-straight", barrier_straight()),
              "corner": shape("l31-barrier-corner", barrier_corner()),
              "post": shape("l31-barrier-post", barrier_post())}
    sel = {"straight": (0, 0, 0, 1, 1, 0.34), "corner": (0, 0, 0, 1, 1, 1), "post": (0, 0, 0, 0.34, 1, 0.34)}
    prop_block("l31-barrier", "Level 31: the rink's barrier along the boards' outer edge (the side named is the skirt's): a thin padded wall, white on the rink side, carpet on the skirt's, a bumper rail and a padded cap; straight, corner (that side and the one to its left) or post (the corner square where two runs meet)",
               lambda k: shapes[k], lambda k: sel[k], lambda k: (0, 0, 0, 1, 1, 0.3) if k == "straight" else sel[k],
               kinds=list(shapes), kindgroup="piece", material="Plastic", resistance=3)
    gshapes = {"leafl": shape("l31-rinkgate-leaf", gate_leaf()), "leafr": shape("l31-rinkgate-leafr", mirror_x(gate_leaf())),
               "sill": shape("l31-rinkgate-sill", gate_sill())}
    prop_block("l31-rinkgate", "Level 31: a gap in the rink's barrier (the side named is the skirt's): leafl / leafr, the end post (at the left or right end, seen from the rink) with the gate swung open into the rink on its hinges; sill, the aluminium threshold; walk-through",
               lambda k: gshapes[k], lambda k: (0, 0, 0, 0.15, 1, 0.3) if k == "leafl" else (0.85, 0, 0, 1, 1, 0.3) if k == "leafr" else (0, 0, 0, 1, 0.05, 0.25), None,
               kinds=list(gshapes), kindgroup="piece", material="Plastic", resistance=2)

    refs = {"deck": djdesk_deck(), "mixer": djdesk_mixer()}
    prop_block("l31-djdesk", "Level 31: the DJ booth, one block of it: a black fascia with lit strips toward the side (the crowd), the desk top at 15 units with a turntable (deck) or the mixer between two CD decks (mixer); the DJ stands behind",
               lambda k: refs[k], (0, 0, 0.03, 1, 0.94, 0.94), (0, 0, 0.03, 1, 0.94, 0.94), kinds=["deck", "mixer"], kindgroup="part",
               extra={"lightHsv": [50, 3, 4]})
    ref = speaker()
    prop_block("l31-speaker", "Level 31: a PA stack, 30 units tall: a sub cabinet with an 18-inch cone under a top cabinet with a 12-inch cone and a horn, steel corners; faces the side",
               lambda k: ref, (0.0625, 0, 0.05, 0.9375, 1, 0.97), (0.0625, 0, 0.05, 0.9375, 1, 0.97), resistance=4)
    ref = truss()
    prop_block("l31-truss", "Level 31: a box truss of aluminium tube under a rink's ceiling, laced, with two par cans on yokes tilted out over the boards (lenses lit), along the axis",
               lambda k: {"base": ref} if k == "we" else {"base": ref, "rotateY": 90}, (0, 0.35, 0.3, 1, 1, 0.7), None,
               kinds=["we", "ns"], kindgroup="axis", oriented=False, resistance=3, extra={"lightHsv": [50, 3, 9]})

    for g, d in GAMES.items():
        cab_art(g, d)
    refs = {g: retrocab(g, d) for g, d in GAMES.items()}
    prop_block("l31-retrocab", "Level 31: a 1980s upright arcade cabinet, 30 units tall (it reaches into the block above): side art and T-moulding, lit marquee, the CRT in its bezel, a sloped control panel, a coin door with lit coin returns; by game and facing side",
               lambda k: refs[k], (0.09, 0, 0.03, 0.91, 1, 0.97), (0.09, 0, 0.03, 0.91, 1, 0.97),
               kinds=list(GAMES), kindgroup="game", resistance=4, extra={"lightHsv": [40, 3, 4]})
    pinball_textures()
    ref = pinball()
    prop_block("l31-pinball", "Level 31: a pinball machine, its front (the flippers' end) toward the side: legs, the sloping cabinet and lit playfield, lock-down bar, plunger, coin door, the lit backglass head at the back (29 units tall)",
               lambda k: ref, (0.1, 0, 0, 0.9, 1, 1), (0.1, 0, 0, 0.9, 0.85, 1), resistance=4, extra={"lightHsv": [50, 4, 6]})
    ref = photobooth()
    prop_block("l31-photobooth", "Level 31: an arcade photo booth, 31 units tall: the curtain in folds over the left half, the lit PHOTO header, sample strips, coin box and print slot on the right, a stool and camera inside; toward the side",
               lambda k: ref, (0, 0, 0, 1, 1, 1), (0, 0, 0, 1, 1, 1), resistance=3, extra={"lightHsv": [8, 3, 5]})
    ref = dispenser()
    prop_block("l31-dispenser", "Level 31: the arcade's green-card machine: a purple cabinet under a lit GREEN CARDS header, a bill acceptor, a big lit button over the card tray; faces the side",
               lambda k: ref, (0.19, 0, 0.25, 0.81, 1, 0.72), (0.19, 0, 0.25, 0.81, 1, 0.72), resistance=3, extra={"lightHsv": [22, 4, 4]})
    ref = slushie()
    prop_block("l31-slushie", "Level 31: a slushie machine on its stainless cabinet, two bowls (blue raspberry, cherry) under a lit SLUSH header, taps and a drip tray, 31 units tall; faces the side",
               lambda k: ref, (0, 0, 0.06, 1, 1, 1), (0, 0, 0.06, 1, 1, 1), resistance=3, extra={"lightHsv": [40, 3, 4]})
    ref = cinemabench()
    prop_block("l31-cinemabench", "Level 31: one segment of the cinema's long continuous steel bench: a perforated seat with a rolled front, a slanted back, a T-leg bolted down, a cup holder on the back for the row behind; the sitter faces the side",
               lambda k: ref, (0, 0, 0.17, 1, 0.9, 0.95), (0, 0, 0.17, 1, 0.44, 0.75))
    ref = mediacab()
    prop_block("l31-mediacab", "Level 31: the cinema TV's low walnut cabinet, two doors and an open shelf (a VCR blinking 12:00, a disc player), the sound bar on top; toward the side",
               lambda k: ref, (0, 0, 0.22, 1, 0.6, 0.94), (0, 0, 0.22, 1, 0.6, 0.94), material="Wood", sounds=WOOD, resistance=3)
    ref = stall()
    prop_block("l31-stall", "Level 31: a toilet stall, laminate partitions on chrome feet with a head rail, the door ajar on three hinges (VACANT), the toilet with lid and cistern against the wall (28 units tall); the door faces the side",
               lambda k: ref, (0, 0, 0, 1, 1, 1), (0, 0, 0, 1, 1, 1), resistance=3)
    ref = vanity()
    prop_block("l31-vanity", "Level 31: a washroom vanity: the basin in a solid top on a cabinet with doors, a mixer tap, a soap pump, a splashback; the basin faces the side (the mirror is an l31-plate over it)",
               lambda k: ref, (0, 0, 0.125, 1, 0.8, 1), (0, 0, 0.125, 1, 0.78, 1), resistance=3)
    ref = popcorn()
    prop_block("l31-popcorn", "Level 31: a kettle popcorn machine on its red cart, the case framed in chrome with popcorn heaped in it and the kettle hung from its roof, the lit POPCORN header, 30 units tall; faces the side",
               lambda k: ref, (0.04, 0, 0.1, 0.96, 1, 0.9), (0.04, 0, 0.1, 0.96, 1, 0.9), resistance=3, extra={"lightHsv": [8, 3, 4]})
    ref = jukebox()
    prop_block("l31-jukebox", "Level 31: a 1990s jukebox, wood under a stepped neon arch, the record window, selector keys, bubble tubes either side, a chrome grille, 22 units tall, toward the side",
               lambda k: ref, (0.03, 0, 0.21, 0.97, 1, 0.82), (0.03, 0, 0.21, 0.97, 1, 0.82), resistance=3, extra={"lightHsv": [50, 4, 6]})
    riser()
    locker_textures()
    lrefs = {k: locker(k) for k in ("lower", "upper")}
    data = {"code": "l31-locker", "variantgroups": [{"code": "part", "states": ["lower", "upper"]}, {"code": "side", "states": SIDES}],
            "shapeByType": {f"l31-locker-{k}-{sd}": ({"base": lrefs[k], "rotateY": ROT[sd]} if ROT[sd] else {"base": lrefs[k]})
                            for k in ("lower", "upper") for sd in SIDES},
            "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
            "blockmaterial": "Metal", "drawtype": "json", "sidesolid": {"all": True}, "sideopaque": {"all": True},
            "lightAbsorption": 99, "resistance": 6, "drops": [], "sounds": METAL}
    write_json(os.path.join(BLOCKS, "l31-locker.json"), data,
               "Level 31: a bank of coin lockers set in the rink's wall (a full wall block), its doors toward the side: two across and two high, "
               "louvres, number plates, coin locks with keys on orange tags, one door ajar in the lower; lower (with the kick base) and upper")
    ref = table()
    prop_block("l31-table", "Level 31: a cafe table, white laminate with a magenta edge band on a chrome column and cross foot, napkins, salt, pepper and ketchup on it (not oriented)", lambda k: ref,
               (0.05, 0, 0.05, 0.95, 0.75, 0.95), (0.05, 0, 0.05, 0.95, 0.75, 0.95), kinds=["plain"], oriented=False, resistance=2)
    dryer()
    neon_tubes()
    lang()


LANG = {
    "block-l31-barrier-*": "Rink Barrier",
    "block-l31-rinkgate-*": "Rink Gate",
    "block-l31-pinball-*": "Pinball Machine",
    "block-l31-slushie-*": "Slushie Machine",
    "block-l31-popcorn-*": "Popcorn Machine",
    "block-l31-locker-*": "Coin Lockers",
}


def lang():
    """Puts LANG into en.json's Level 31 block (as gen_31_content.merge_lang: a key there is updated in place, a new one
    goes at the end of the block)."""
    import json
    import re
    nl, tab = chr(10), chr(9)
    en = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "backrooms", "lang", "en.json")
    with open(en, encoding="utf-8") as f:
        lines = f.read().split(nl)
    start = next(i for i, l in enumerate(lines) if l.startswith(tab + '"level-24"'))
    ours = re.compile(r'^\t"(level-24\d\d|levelhint-24|levelname-24|[^"]*l31-[^"]*)"\s*:')
    end = start
    while end + 1 < len(lines) and ours.match(lines[end + 1]):
        end += 1
    block = lines[start:end + 1]
    keys = {}
    for i, l in enumerate(block):
        m = re.match(r'^\t"([^"]+)"\s*:', l)
        if m:
            keys[m.group(1)] = i
    for k, v in LANG.items():
        entry = tab + json.dumps(k) + ": " + json.dumps(v, ensure_ascii=False) + ","
        if k in keys:
            block[keys[k]] = entry
        else:
            keys[k] = len(block)
            block.append(entry)
    lines[start:end + 1] = block
    text_ = nl.join(lines)
    json.loads(text_)
    with open(en, "w", encoding="utf-8", newline=nl) as f:
        f.write(text_)


def main():
    blocks()
    print("Level 31 round 4: textures in", os.path.relpath(TEX), "; blocktypes in", os.path.relpath(BLOCKS))


if __name__ == "__main__":
    main()
