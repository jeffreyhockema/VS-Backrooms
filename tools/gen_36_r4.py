"""Level 36 "Airport" (experimental): round 4's blocks (2026-11-02, the asset-quality pass).

Structure (textures in textures/block/36/props/, JSON models):
    l36-frame-{q}                   the space-frame ceiling over the claim hall, security, the concourses and the piers: a
                                    dark acoustic deck with a white tube frame hung under it, square on square, 2 x 2 blocks
                                    a module; q = the block's parity in the module (x then z: ee oe eo oo), so the top nodes
                                    sit on even block corners and the bottom nodes on odd ones, one diagonal through each block
    l36-colfoot-{quad} / l36-colhead-{quad}
                                    a 2 x 2 column's cladding: a stainless plinth at its foot, a stepped capital flaring into
                                    the ceiling at its head; quad = the block's corner of the column (nw ne sw se), the plinth
                                    and the capital on its two outer faces
    l36-bridge-{part}-{side}        the jet bridge's walls, the bridge on <side>: lower (corrugated panel, a handrail on
                                    brackets, a rubber skirting), glass (the glazed band: a sill, a header, a mullion, a
                                    tinted pane, the apron and the parked plane's flank beyond it), upper (panel, an LED cove)
    l36-bridgefloor / l36-bridgeceil   the bridge's studded rubber floor and its ribbed ceiling (cubes)
Props (models facing north, turned by side):
    l36-coffee-{side}               a cafe's back counter with an espresso machine (two group heads, a steam wand, cups
                                    warming on top), a grinder and a knock box; the front toward the barista's customers
    l36-pastry-{side}               a cafe's front counter: a glass display case of cakes and pastries on a wood-fronted base
    l36-till-{side}                 a shop's till counter: the register, its screen toward the clerk, a card reader, bags
    l36-stool                       a chrome bar stool, a round red seat, a foot ring
    l36-trolley-{side}              an airport luggage trolley: a frame on four castors, a deck, a basket and a handle bar

Run (from the repo root, under the asset lock): bash tools/locked.sh run python tools/gen_36_r4.py  (gen_36.py runs it)
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matlib as M  # noqa: E402
import gen_36_props as P  # noqa: E402
import gen_36_props_tex as TX  # noqa: E402

B = P.B
no = P.no
S = 32
SIDES = ("north", "east", "south", "west")


# ======================================================================== Textures

def _arr(img):
    return np.asarray(img.convert("RGBA")).astype(np.float64)


def _img(a):
    a = np.clip(np.rint(a), 0, 255).astype(np.uint8)
    a[..., 3] = np.where(a[..., 3] > 127, 255, 0) if a.shape[2] == 4 else 255
    return Image.fromarray(a, "RGBA")


def textures():
    s = TX.seed_of("r4")
    # brushed aluminium (fascia trims), the hazard stripes of the belt's lintel, the curtain's rubber strips
    TX.save(M.brushed_metal(s, base=(200, 204, 210), direction="h", streak=6, sheen=12), "r4-alu")
    img = Image.new("RGBA", (S, S), (240, 196, 30, 255))
    d = ImageDraw.Draw(img)
    for k in range(-S, S * 2, 8):
        d.polygon([(k, 0), (k + 4, 0), (k + 4 - S, S), (k - S, S)], fill=(30, 30, 32, 255))
    img = M.grime(img, 0.18, s + 1, cover=0.4)
    TX.save(img, "r4-hazard")
    strip = M.rubber(seed=s + 2, base=(34, 34, 36), grain=2, mottle=3)
    a = _arr(strip)
    a[26:32, :, :3] *= 0.75   # the strips' bottom ends, scuffed dark by the bags
    a[0:3, :, :3] += 14
    TX.save(_img(a), "r4-strip")
    # the space frame: white painted tube with a faint seam; the deck: a dark grey perforated acoustic deck with ribs
    tube = M.painted_metal(s + 3, base=(232, 234, 236), grain=2, mottle=2, panel=False, chips=0)
    a = _arr(tube)
    a[:, 0:4, :3] += 8
    a[:, 26:32, :3] -= 22
    TX.save(_img(a), "r4-tube")
    node = M.brushed_metal(s + 4, base=(176, 180, 186), direction="h", streak=4, sheen=10)
    TX.save(node, "r4-node")
    deck = M.noise_hv((62, 64, 70), 2, s + 5, S, 3, (16, 8))
    a = _arr(deck)
    for y in range(1, S, 4):
        for x in range((y // 4) % 2 * 2 + 1, S, 4):
            a[y, x, :3] -= 18
    for x in (0, 16):
        a[:, x, :3] -= 26
        a[:, x + 1, :3] += 10
    TX.save(_img(a), "r4-deck")
    # column cladding white with a soft vertical sheen; plinth stainless
    col = M.painted_metal(s + 6, base=(236, 236, 232), grain=2, mottle=2, panel=False, chips=0)
    a = _arr(col)
    a[:, 0:2, :3] -= 16
    a[:, 30:32, :3] -= 22
    TX.save(_img(a), "r4-colclad")
    # the jet bridge: corrugated grey-beige panel (vertical ribs), a scuffed rubber skirting, the studded floor, the ceiling
    pan = M.painted_metal(s + 7, base=(178, 176, 168), grain=2, mottle=4, panel=False, chips=2)
    a = _arr(pan)
    for x in range(0, S, 8):
        a[:, x:x + 2, :3] += 18
        a[:, x + 5:x + 8, :3] -= 16
    a[26:32, :, :3] -= 10   # dirt toward the foot
    TX.save(_img(a), "r4-bridgepanel")
    flo = M.rubber(seed=s + 8, base=(70, 72, 76), grain=2, mottle=4)
    a = _arr(flo)
    for y in range(2, S, 6):
        for x in range((y // 6) % 2 * 3 + 2, S, 6):
            a[y:y + 2, x:x + 2, :3] += 22
            a[y + 2, x:x + 2, :3] -= 18
    a[:, 0, :3] -= 18
    TX.save(_img(a), "r4-bridgefloor")
    ceil = M.painted_metal(s + 9, base=(210, 208, 202), grain=2, mottle=2, panel=False, chips=0)
    a = _arr(ceil)
    for y in range(0, S, 8):
        a[y, :, :3] -= 30
        a[y + 1, :, :3] += 10
    a[12:20, 12:20, :3] = (250, 248, 236)
    a[11, 11:21, :3] -= 40
    a[20, 11:21, :3] -= 40
    TX.save(_img(a), "r4-bridgeceil")
    # the view out of the bridge's glazing: wet grey apron, the stand's painted lines, fog, a plane's white flank and a window row
    v = np.zeros((S, S, 4))
    v[..., 3] = 255
    for y in range(S):
        if y < 13:
            v[y, :, :3] = np.array((176, 182, 188)) + y * 0.8
        else:
            v[y, :, :3] = np.array((96, 98, 100)) - (y - 13) * 0.6
    v[13, :, :3] = (140, 146, 150)
    v[22, :, :3] = (196, 170, 60)    # the stand's lead-in line
    v[27:29, :, :3] = (210, 210, 206)
    v[6:14, 18:32, :3] = (226, 228, 232)    # the plane's flank, parked beyond
    v[9:11, 19:32:3, :3] = (60, 70, 86)
    v[13, 18:32, :3] = (120, 124, 130)
    rng = np.random.default_rng(s)
    v[..., :3] += rng.normal(0, 2.0, (S, S, 1))
    TX.save(_img(v), "r4-bridgeview")
    gl = np.zeros((S, S, 4))
    gl[..., :3] = (170, 196, 204)
    gl[..., 3] = 60
    for k in range(0, S):   # one soft diagonal sheen, not streaks
        x = (k + 6) % S
        gl[k, x:x + 3, :3] += 30
        gl[k, x:x + 3, 3] = 84
    TX.save(Image.fromarray(np.clip(gl, 0, 255).astype(np.uint8), "RGBA"), "r4-glass")
    led = Image.new("RGBA", (S, S), (250, 246, 226, 255))
    TX.save(led, "r4-led")
    # cafe: espresso machine's red enamel, the grinder's beans in the hopper, cakes, wood counter front, the till's screen
    TX.save(M.painted_metal(s + 10, base=(168, 34, 30), grain=2, mottle=3, panel=False, chips=1), "r4-enamel")
    beans = M.noise_hv((74, 44, 26), 8, s + 11, S, 6, (4, 2))
    TX.save(beans, "r4-beans")
    TX.save(M.wood_planks(s + 12, size=S, base=(120, 80, 50), planks=4, direction="v", grain=3, contrast=0.9), "r4-woodv")
    for i, (c1, c2) in enumerate((((236, 208, 160), (120, 60, 40)), ((250, 240, 236), (220, 120, 140)),
                                  ((90, 50, 34), (60, 34, 24)), ((214, 160, 80), (250, 236, 200)))):
        img = M.noise_hv(c1, 3, s + 20 + i, S, 3, (8, 4))
        a = _arr(img)
        a[0:6, :, :3] = c2
        a[12:15, :, :3] = np.array(c2) * 0.9
        TX.save(_img(a), f"r4-cake{i}")
    scr = Image.new("RGBA", (S, S), (16, 20, 28, 255))
    d = ImageDraw.Draw(scr)
    d.rectangle((2, 2, 29, 7), fill=(30, 110, 180, 255))
    for y in (11, 16, 21):
        d.rectangle((3, y, 20, y + 2), fill=(170, 180, 190, 255))
        d.rectangle((24, y, 28, y + 2), fill=(240, 200, 60, 255))
    d.rectangle((3, 26, 28, 29), fill=(40, 170, 90, 255))
    TX.save(scr, "r4-tillscreen")
    TX.save(M.noise_hv((200, 30, 36), 3, s + 13, S, 3, (8, 4)), "r4-redvinyl")
    # trolley: galvanised wire basket (a grid, see-through), the deck's tread
    basket = np.zeros((S, S, 4))
    basket[..., :3] = (176, 180, 186)
    for k in range(0, S, 4):
        basket[k, :, 3] = 255
        basket[:, k, 3] = 255
    TX.save(Image.fromarray(basket.astype(np.uint8), "RGBA"), "r4-wire")
    # the gallery: dark tinted glazing onto an upper level nobody reaches (a shop's dim shelves, a dark doorway, a
    # reflection band); its slab's white soffit with a row of downlights
    g = np.zeros((S, S, 4))
    g[..., 3] = 255
    for y in range(S):
        g[y, :, :3] = np.array((34, 40, 50)) + (S - y) * 0.5
    rng = np.random.default_rng(s + 30)
    for x0 in (3, 18):
        for yy in (10, 17, 24):
            g[yy, x0:x0 + 10, :3] = (58, 62, 70)
            for x in range(x0, x0 + 10, 2):
                h = int(rng.integers(2, 5))
                g[yy - h:yy, x, :3] = rng.integers(50, 96, 3)
    g[2:5, :, :3] += 26   # the reflection band of the hall's lights
    g[:, 15:17, :3] = (24, 26, 30)
    TX.save(_img(g), "r4-gallery")
    so = M.painted_metal(s + 31, base=(228, 228, 224), grain=2, mottle=2, panel=False, chips=0)
    a = _arr(so)
    for x in (6, 22):
        a[12:20, x:x + 4, :3] = (252, 250, 236)
    TX.save(_img(a), "r4-soffit")
    # magazine covers (a newsstand's rack): mastheads, a cover photo block, coverlines; four mixes
    rng = random.Random(3604)
    for n in range(4):
        img = Image.new("RGBA", (S, S), (20, 20, 22, 255))
        d = ImageDraw.Draw(img)
        for i in range(4):
            x0 = i * 8
            bg = rng.choice(((236, 236, 230), (214, 40, 46), (30, 60, 140), (250, 210, 40), (20, 20, 24), (60, 150, 90)))
            d.rectangle((x0, 0, x0 + 7, 31), fill=bg + (255,))
            d.rectangle((x0 + 1, 1, x0 + 6, 4), fill=rng.choice(((255, 255, 255), (200, 20, 30), (10, 10, 10))) + (255,))
            ph = tuple(rng.randint(60, 200) for _ in range(3))
            d.rectangle((x0 + 1, 6, x0 + 6, 22), fill=ph + (255,))
            d.rectangle((x0 + 2, 9, x0 + 5, 21), fill=tuple(max(0, c - 40) for c in ph) + (255,))
            for y in (24, 27):
                d.rectangle((x0 + 1, y, x0 + rng.randint(3, 6), y + 1), fill=(250, 250, 250, 255) if sum(bg) < 300 else (30, 30, 30, 255))
            d.line((x0 + 7, 0, x0 + 7, 31), fill=(10, 10, 10, 255))
        TX.save(img, f"r4-mags{n}")
    # the fire cabinet: red label FIRE / an extinguisher's red body
    lab = Image.new("RGBA", (S, S), (196, 28, 32, 255))
    TX.centre_text(lab, "FIRE", 6, (255, 255, 255))
    TX.centre_text(lab, "EXTINGUISHER", 18, (255, 255, 255))
    TX.save(lab, "r4-firelabel")
    TX.save(M.painted_metal(s + 40, base=(190, 26, 30), grain=2, mottle=3, panel=False, chips=1), "r4-red")
    # a prayer mat: a deep red field, a cream border, a niche (mihrab) arch toward the top, a fringe at the ends
    mat = M.fabric(seed=s + 50, base=(132, 28, 34), weave="plain", contrast=8, grain=2, mottle=4)
    d = ImageDraw.Draw(mat)
    d.rectangle((1, 1, 30, 30), outline=(226, 206, 160, 255))
    d.rectangle((3, 3, 28, 28), outline=(36, 60, 96, 255))
    d.polygon([(9, 24), (9, 12), (16, 6), (23, 12), (23, 24)], outline=(226, 206, 160, 255))
    d.line((16, 14, 16, 22), fill=(226, 206, 160, 255))
    TX.save(mat, "r4-prayermat")
    # the information pylon's lit face: the white "i" on airport yellow, INFORMATION under it
    inf = Image.new("RGBA", (S, S), (250, 196, 20, 255))
    d = ImageDraw.Draw(inf)
    d.ellipse((13, 3, 18, 8), fill=(30, 30, 34, 255))
    d.rectangle((13, 11, 18, 24), fill=(30, 30, 34, 255))
    d.rectangle((11, 22, 20, 24), fill=(30, 30, 34, 255))
    d.rectangle((11, 11, 14, 12), fill=(30, 30, 34, 255))
    TX.save(inf, "r4-info")
    touch = Image.new("RGBA", (S, S), (14, 30, 60, 255))
    d = ImageDraw.Draw(touch)
    d.rectangle((2, 2, 29, 6), fill=(250, 196, 20, 255))
    for i, y in enumerate((10, 16, 22)):
        d.rectangle((3, y, 14, y + 4), fill=(40, 90, 160, 255))
        d.rectangle((17, y, 28, y + 4), fill=(40, 90, 160, 255))
    TX.save(touch, "r4-touch")
    # luggage: hard-shell polycarbonate (ribbed, four colours), a canvas duffel, a garment bag, a luggage tag
    for i, c in enumerate(((40, 70, 130), (170, 40, 44), (200, 204, 210), (34, 36, 40))):
        img = M.noise_hv(c, 2, s + 60 + i, S, 2, (16, 8))
        a = _arr(img)
        for x in range(2, S, 6):
            a[:, x, :3] += 22
            a[:, x + 1, :3] -= 14
        a[:, 0:1, :3] -= 18
        TX.save(_img(a), f"r4-shell{i}")
    TX.save(M.fabric(seed=s + 64, base=(74, 84, 56), weave="basket", contrast=8, grain=2, mottle=5), "r4-canvas")
    TX.save(M.fabric(seed=s + 65, base=(40, 42, 50), weave="plain", contrast=6, grain=2, mottle=3), "r4-garment")
    tag = Image.new("RGBA", (S, S), (240, 238, 228, 255))
    d = ImageDraw.Draw(tag)
    d.rectangle((0, 0, 31, 9), fill=(92, 44, 142, 255))
    for y in (13, 18, 23):
        d.rectangle((3, y, 28, y + 1), fill=(60, 60, 64, 255))
    TX.save(tag, "r4-tag")
    # a first-class lounge's cognac leather: a soft grain, a little shine on the top edge, darker in the creases
    lea = M.noise_hv((132, 74, 40), 4, s + 70, S, 5, (8, 4))
    a = _arr(lea)
    a[0:2, :, :3] += 16
    a[30:32, :, :3] -= 18
    TX.save(_img(a), "r4-cognac")
    # a restroom mirror: the cool grey of the room behind, a pale diagonal sheen, a little desilvering at the foot
    mi = np.zeros((S, S, 4))
    mi[..., 3] = 255
    for y in range(S):
        mi[y, :, :3] = np.array((150, 162, 168)) + (S - y) * 0.6
    for k in range(S):
        mi[k, (S - k + 4) % S:(S - k + 8) % S or S, :3] += 30
    mi[28:32, ::3, :3] -= 40
    TX.save(_img(mi), "r4-mirror")
    # the kiosks' canopy soffit: the Agency's purple gloss with a round downlight in a white trim ring
    can = M.noise_hv((92, 44, 142), 2, s + 41, S, 3, (16, 8))
    a = _arr(can)
    yy, xx = np.mgrid[0:S, 0:S]
    r = np.hypot(xx - 15.5, yy - 15.5)
    a[(r < 7.5) & (r >= 5.5), :3] = (230, 230, 226)
    a[r < 5.5, :3] = (255, 250, 232)
    a[0, :, :3] -= 20
    a[:, 0, :3] -= 20
    TX.save(_img(a), "r4-canopy")
    a = _arr(M.noise_hv((92, 44, 142), 2, s + 41, S, 3, (16, 8)))
    a[0, :, :3] -= 20
    a[:, 0, :3] -= 20
    TX.save(_img(a), "r4-canopyplain")
    # the roof lights between the frame's tubes: gen_36_detail.py's overcast skylight, its mullions as the deck's
    TX.save(Image.open(os.path.join(os.path.dirname(TX.TEX), "l36-finish-skylight.png")).convert("RGBA"), "r4-skydeck")
    # the hall's travertine (gen_36_detail.py's l36-finish-stone), for the fire cabinet's wall cube
    TX.save(Image.open(os.path.join(os.path.dirname(TX.TEX), "l36-finish-stone.png")).convert("RGBA"), "r4-stone")


# ======================================================================== Shapes

def frame(q):
    """One block of the space frame. q[0] / q[1]: 'e' if the block's x / z is even. The top node is on the even corner
    (x = 0 if x even else 16; the same for z), the bottom node on the opposite (odd) corner."""
    ex = 0 if q[0] == "e" else 16
    ez = 0 if q[1] == "e" else 16
    ox, oz = 16 - ex, 16 - ez
    yt, yb = 11.25, 2.25   # the top and bottom chords' centre lines
    t = 0.7   # a half chord's thickness (the neighbour holds the other half)
    deck = B("Deck", (0, 13, 0), (16, 16, 16), "r4-deck", faces=("down",))
    els = [deck]

    def half(lo, edge):
        return (edge, edge + t) if edge == 0 else (edge - t, edge)
    # top chords along the even lines (x = ex and z = ez), bottom chords along the odd ones
    for name, y, xe, ze in (("Top", yt, ex, ez), ("Bot", yb, ox, oz)):
        x1, x2 = half(None, xe)
        # (each half drops its face on the block boundary: the neighbour's half continues the tube there)
        bx = "west" if xe == 0 else "east"
        bz = "north" if ze == 0 else "south"
        els.append(B(f"{name}X", (x1, y - t, 0), (x2, y + t, 16), "r4-tube", faces=no(bx)))
        z1, z2 = half(None, ze)
        els.append(B(f"{name}Z", (0, y - t, z1), (16, y + t, z2), "r4-tube", faces=no(bz)))
        n1, n2 = (xe, xe + 1.4) if xe == 0 else (xe - 1.4, xe)
        m1, m2 = (ze, ze + 1.4) if ze == 0 else (ze - 1.4, ze)
        els.append(B(f"{name}Node", (n1, y - 1.3, m1), (n2, y + 1.3, m2), "r4-node", faces=no(bx, bz)))
    # hangers from the deck to the top node's chords
    hx1, hx2 = (ex, ex + 0.5) if ex == 0 else (ex - 0.5, ex)
    hz1, hz2 = (ez, ez + 0.5) if ez == 0 else (ez - 0.5, ez)
    els.append(B("Hanger", (hx1, yt + 1.3, hz1), (hx2, 13, hz2), "r4-node", faces=no("up", "down")))
    # the diagonal, top node to bottom node, built along +x and turned: first tilted down (Z), then swung into plan (Y)
    dx, dz = (1 if ox > ex else -1), (1 if oz > ez else -1)
    run = math.hypot(16, 16)
    drop = yt - yb
    length = math.hypot(run, drop)
    tilt = -math.degrees(math.atan2(drop, run))
    yaw = math.degrees(math.atan2(-dz, dx))
    diag = B("Diag", (ex, yt - 0.55, ez - 0.55), (ex + length, yt + 0.55, ez + 0.55), "r4-tube", faces=no("east", "west"))
    diag["rotationOrigin"] = [ex, yt, ez]
    diag["rotationZ"] = round(tilt, 3)
    diag["rotationY"] = round(yaw, 3)
    els.append(diag)
    return els


def framesky(q):
    """(round 4) A space-frame block whose deck is a roof light: the overcast sky through the glazing, glowing."""
    els = frame(q)
    els[0] = B("Deck", (0, 13, 0), (16, 16, 16), "r4-skydeck", faces=("down",), glow=120)
    return els


def framelight(q, state):
    """(round 4) A space-frame block with a linear pendant light hung from its chords: a dark housing on two cables, its
    diffuser lit underneath (off: dead)."""
    els = frame(q)
    lit = state != "off"
    els += [B("Cable0", (4, 5.5, 7.75), (4.4, 13, 8.15), "darksteel", faces=no("up", "down")),
            B("Cable1", (11.6, 5.5, 7.75), (12, 13, 8.15), "darksteel", faces=no("up", "down")),
            B("Housing", (2, 4, 6), (14, 5.5, 10), "darksteel", faces=no("down")),
            B("Diffuser", (2.25, 3.6, 6.25), (13.75, 4, 9.75), "r4-led" if lit else "r4-node", faces=("down", "north", "south", "east", "west"),
              glow=200 if lit else 0)]
    return els


QUAD_OUT = {"nw": ("north", "west"), "ne": ("north", "east"), "sw": ("south", "west"), "se": ("south", "east")}


def _bands(quad, steps, tex, tag="B"):
    """Bands standing out of the block's outer faces: steps [(y1, y2, out)]; the north/south band runs past the corner."""
    out = QUAD_OUT[quad]
    els = []
    for i, (y1, y2, k) in enumerate(steps):
        for f in out:
            if f in ("north", "south"):
                x1 = -k if "west" in out else 0
                x2 = 16 + k if "east" in out else 16
                z1, z2 = (-k, 0) if f == "north" else (16, 16 + k)
                faces = (f, "up", "down") + (("west",) if "west" in out else ("east",))
            else:
                x1, x2 = (-k, 0) if f == "west" else (16, 16 + k)
                z1, z2 = 0, 16
                faces = (f, "up", "down")
            els.append(B(f"{tag}{i}{f[0]}", (x1, y1, z1), (x2, y2, z2), tex, faces=faces))
    return els


def colfoot(quad):
    return ([B("Clad", (0, 0, 0), (16, 16, 16), "r4-colclad", faces=QUAD_OUT[quad])] +
            _bands(quad, [(0, 2.5, 1.0), (2.5, 3, 0.5)], "steel"))


def colhead(quad):
    return ([B("Clad", (0, 0, 0), (16, 16, 16), "r4-colclad", faces=QUAD_OUT[quad])] +
            _bands(quad, [(8, 9, 0.5), (11, 13, 1.25), (13, 16, 2.25)], "r4-colclad") +
            _bands(quad, [(10.25, 11, 0.9)], "steel", "S"))


def bridge(part):
    """A jet bridge's wall, the bridge to the north (-z)."""
    if part == "lower":
        els = [B("Panel", (0, 0, 2), (16, 16, 16), "r4-bridgepanel", faces=("north",)),
               B("Skirt", (0, 0, 1.25), (16, 2, 2), "rubber", faces=("north", "up")),
               B("Rail", (0, 13, 0.25), (16, 14.25, 1.25), "chrome", faces=("north", "up", "down", "south")),
               B("Rib", (0, 2, 1.5), (0.75, 16, 2), "darksteel", faces=("north", "east", "west"))]
        for i, x in enumerate((4, 12)):
            els.append(B(f"Bracket{i}", (x - 0.5, 12.5, 1.25), (x + 0.5, 13.25, 2), "chrome", faces=no("south")))
        return els
    if part == "glass":
        # (round 4, after the shots: shallow, the view just behind the pane; a deep recess read as grey boxes down the run)
        pane = P.transparent(B("Pane", (0.75, 2, 2.75), (16, 14, 3.25), "r4-glass", faces=("north", "south")))
        return [B("View", (0, 2, 4.5), (16, 14, 5), "r4-bridgeview", faces=("north",)),
                B("Sill", (0, 0, 1.5), (16, 2, 5), "r4-bridgepanel", faces=("north", "up")),
                B("SillCap", (0, 1.75, 1), (16, 2.25, 3.25), "darksteel", faces=("north", "up")),
                B("Header", (0, 14, 1.5), (16, 16, 5), "r4-bridgepanel", faces=("north", "down")),
                B("Mullion", (0, 2, 1.5), (0.75, 14, 4.5), "darksteel", faces=("north", "east", "west")),
                B("BeadT", (0.75, 13.5, 2.25), (16, 14, 2.75), "darksteel", faces=("north", "down")),
                B("BeadB", (0.75, 2, 2.25), (16, 2.5, 2.75), "darksteel", faces=("north", "up")), pane]
    return [B("Panel", (0, 0, 2), (16, 16, 16), "r4-bridgepanel", faces=("north",)),
            B("Cove", (0, 13.5, 0.5), (16, 14.5, 2), "darksteel", faces=("north", "down")),
            P.glow([B("Led", (0, 14.5, 1.25), (16, 15, 2), "r4-led", faces=("north", "down"))], 220)[0],
            B("Rib", (0, 0, 1.5), (0.75, 13.5, 2), "darksteel", faces=("north", "east", "west"))]


def gallery(part):
    """(round 4) The gallery round the tall halls, on a wall's face toward the hall (north): lip, a slab edge standing out
    of the wall with a glass balustrade and a handrail on it; glass, the upper level's dark glazing behind mullions."""
    if part == "lip":
        els = [B("Wall", (0, 0, 0), (16, 16, 16), "r4-colclad", faces=("north",)),
               B("Slab", (0, 0, -4), (16, 3.5, 0), {"front": "r4-colclad", "top": "r4-bridgefloor", "bottom": "r4-soffit", "side": "r4-colclad"},
                 faces=("north", "up", "down")),
               B("Nosing", (0, 3.5, -4), (16, 4, -3.25), "steel", faces=("north", "up")),
               P.transparent(B("Pane", (0, 4, -3.75), (16, 13.5, -3.25), "r4-glass", faces=("north", "south"))),
               B("Shoe", (0, 4, -4), (16, 5, -3), "darksteel", faces=("north", "south", "up")),
               B("Rail", (0, 13.5, -4.25), (16, 14.5, -2.75), "chrome", faces=("north", "south", "up", "down")),
               B("Post", (0, 4, -3.9), (0.6, 13.5, -3.1), "chrome", faces=no("up", "down"))]
        return els
    return [B("Glazing", (0, 0, 1), (16, 16, 16), "r4-gallery", faces=("north",)),
            B("Mullion", (0, 0, 0), (0.75, 16, 1), "darksteel", faces=("north", "east", "west")),
            B("Transom", (0, 0, 0.25), (16, 0.75, 1), "darksteel", faces=("north", "up")),
            B("Head", (0, 15.25, 0.25), (16, 16, 1), "darksteel", faces=("north", "down"))]


def magrack():
    """(round 4) A newsstand's magazine rack: four sloping tiers of covers on a white steel frame, papers in a bin below."""
    els = [B("Base", (0.5, 0, 6), (15.5, 4, 15.5), "white", faces=no("down")),
           B("Back", (0.5, 4, 14.5), (15.5, 26, 15.5), "white"),
           B("SideL", (0, 0, 4), (0.75, 26, 15.5), "white"),
           B("SideR", (15.25, 0, 4), (16, 26, 15.5), "white"),
           B("Papers", (1.5, 4, 7), (14.5, 6.5, 13), {"top": "worktop", "all": "white"})]
    for i, y in enumerate((6, 11, 16, 21)):
        z = 9 - i * 1.0
        mag = B(f"Mags{i}", (0.75, y, z), (15.25, y + 5, z + 0.75), {"front": f"r4-mags{i % 4}", "all": "white"}, faces=no("down"))
        mag["faces"]["north"]["uv"] = [0, 0, 16, 16]
        els += P.turned([mag], rx=-14, origin=(8, y, z + 0.75))
        els.append(B(f"Lip{i}", (0.75, y - 0.5, z - 0.75), (15.25, y + 1, z), "chrome", faces=no()))
        els.append(B(f"Tier{i}", (0.75, y - 1, z), (15.25, y - 0.25, 14.5), "white", faces=("up", "down")))
    return els


def firecab():
    """(round 4) A fire cabinet recessed in a hall's travertine dado (the wall cube itself): a stainless frame, the red
    extinguisher behind a glass door, its red label over it; the upper part the label and the cabinet's head."""
    stone = {"all": "r4-stone"}
    return [B("Wall", (0, 0, 0), (16, 16, 16), stone, faces=("north", "up", "down", "east", "west", "south")),
            B("Frame", (3, 2, -0.5), (13, 15, 0), "steel", faces=("north", "up", "down", "east", "west")),
            B("Recess", (4, 3, -0.25), (12, 14, -0.2), "darksteel", faces=("north",)),
            B("Body", (6.5, 4, -2.25), (9.5, 11.5, -0.25), "r4-red", faces=no("south")),
            B("Neck", (7.25, 11.5, -1.75), (8.75, 12.5, -0.75), "r4-red", faces=no("south", "down")),
            B("Valve", (6.75, 12.5, -1.75), (9.25, 13.25, -0.75), "black", faces=no("south")),
            B("Hose", (9.25, 6, -1.75), (10, 12.75, -1), "black", faces=no("south")),
            B("Gauge", (7.25, 9, -2.4), (8.75, 10.5, -2.25), "white", faces=("north",)),
            P.transparent(B("Door", (3.5, 2.5, -0.75), (12.5, 14.5, -0.5), "r4-glass", faces=("north", "south"))),
            B("Handle", (11, 7, -1.25), (11.5, 10, -0.75), "chrome", faces=no("south")),
            P.pic(B("Label", (3, 15, -0.75), (13, 16, 0), "r4-red", faces=("north", "up", "east", "west")), "north", "r4-firelabel", glow=60)]


def prayermat(kind):
    """(round 4) A prayer mat laid on the floor toward the room's back wall (north), or one rolled up at the row's end."""
    if kind == "laid":
        mat = B("Mat", (2.5, 0, 0.5), (13.5, 0.35, 15.5), {"top": "r4-prayermat", "all": "r4-prayermat"}, faces=no("down"))
        mat["faces"]["up"]["uv"] = [0, 0, 16, 16]
        return [mat, B("FringeN", (3, 0, 0), (13, 0.2, 0.5), "worktop", faces=("up", "north")),
                B("FringeS", (3, 0, 15.5), (13, 0.2, 16), "worktop", faces=("up", "south"))]
    return P.octagon("Roll", 8, 8, 1.6, 2.5, 13.5, {"top": "worktop", "bottom": "worktop", "side": "r4-prayermat"})


def infopylon():
    """(round 4) An information pylon: a slim column, its lit yellow "i" panel on top, a slanted touch screen at waist
    height facing the hall (north)."""
    els = [B("Foot", (4, 0, 5), (12, 1, 11), "darksteel", faces=no("down")),
           B("Column", (5, 1, 6), (11, 24, 10), {"front": "steel", "side": "darkplastic", "back": "darkplastic", "top": "darksteel"}),
           B("Head", (3, 24, 6.5), (13, 31, 9.5), "darksteel"),
           P.pic(B("InfoN", (3.5, 24.5, 6.25), (12.5, 30.5, 6.5), "darksteel", faces=("north",)), "north", "r4-info", glow=180),
           P.pic(B("InfoS", (3.5, 24.5, 9.5), (12.5, 30.5, 9.75), "darksteel", faces=("south",)), "south", "r4-info", glow=180)]
    screen = [B("Bezel", (3.5, 12, 3), (12.5, 17, 6), "darkplastic"),
              P.pic(B("Touch", (4, 12.5, 2.75), (12, 16.5, 3), "black", faces=("north",)), "north", "r4-touch", glow=140)]
    els += P.turned(screen, rx=25, origin=(8, 12, 6))
    return els


def luggage(kind):
    """(round 4) Luggage nobody came for, lying on a belt's plates or the floor (north the way it points): a hard-shell
    spinner on its side (ribbed shell, a seam, the handle, four wheels, a tag), a canvas duffel, a folded garment bag, a
    second spinner standing up with its handle out."""
    if kind in ("spin0", "spin1"):
        c = "r4-shell0" if kind == "spin0" else "r4-shell1"
        els = [B("ShellA", (2, 0.75, 1.5), (14, 3.5, 14.5), {"top": c, "side": c, "front": c, "back": c, "bottom": "darkplastic"}),
               B("ShellB", (2, 3.75, 1.5), (14, 6.5, 14.5), {"top": c, "side": c, "front": c, "back": c, "bottom": "darkplastic"}),
               B("Seam", (1.85, 3.5, 1.35), (14.15, 3.75, 14.65), "darkplastic", faces=no("up", "down")),
               B("Handle", (6, 2.5, 0.75), (10, 4.75, 1.5), "darkplastic", faces=no("south")),
               B("Grip", (6.5, 6.5, 6.5), (9.5, 7.25, 9.5), "darkplastic", faces=no("down")),
               B("Tag", (10.5, 4.5, 0.25), (12.5, 7, 0.4), "r4-tag", faces=("north", "south"))]
        for i, (x, z) in enumerate(((2.5, 15), (12.5, 15), (2.5, 14.5), (12.5, 14.5))[:2]):
            els.append(B(f"Wheel{i}", (x, 1, z - 0.5), (x + 1, 2.5, z + 0.5), "rubber"))
        els += [B("Foot0", (3, 0, 2.5), (5, 0.75, 4), "darkplastic"), B("Foot1", (11, 0, 2.5), (13, 0.75, 4), "darkplastic")]
        return P.turned(els, ry=-9, origin=(8, 0, 8))
    if kind == "duffel":
        return [B("Body", (1.5, 0, 4.5), (14.5, 5.5, 11.5), {"top": "r4-canvas", "side": "r4-canvas", "front": "r4-canvas", "back": "r4-canvas", "bottom": "r4-canvas"}),
                B("Round", (1.5, 1, 3.75), (14.5, 4.5, 12.25), "r4-canvas", faces=no("up", "down")),
                B("EndW", (1, 1, 5), (1.5, 5, 11), "strap", faces=no("east")),
                B("EndE", (14.5, 1, 5), (15, 5, 11), "strap", faces=no("west")),
                B("Zip", (2, 5.5, 7.6), (14, 5.75, 8.4), "black", faces=no("down")),
                B("StrapA", (5, 5.5, 6), (5.75, 7, 10), "strap", faces=no("down")),
                B("StrapB", (10.25, 5.5, 6), (11, 7, 10), "strap", faces=no("down")),
                B("Handle", (5, 7, 7.5), (11, 7.75, 8.5), "strap")]
    if kind == "garment":
        return P.turned([B("Bag", (1.5, 0, 2), (14.5, 2.25, 14), {"top": "r4-garment", "all": "r4-garment"}),
                         B("Fold", (1.5, 2.25, 2), (14.5, 3, 7), "r4-garment"),
                         B("Hook", (7.5, 0.5, 14), (8.5, 1.5, 16.5), "chrome"),
                         B("Tag", (3, 3, 3), (5.5, 3.1, 5.5), "r4-tag", faces=("up",))], ry=14, origin=(8, 0, 8))
    # standing up, its handle pulled out
    c = "r4-shell2"
    return [B("Shell", (3, 0.75, 5), (13, 15, 11), {"top": c, "side": c, "front": c, "back": c, "bottom": "darkplastic"}),
            B("Seam", (2.85, 0.75, 7.9), (13.15, 15, 8.1), "darkplastic", faces=no("up", "down")),
            B("RodL", (4.5, 15, 9.5), (5.25, 24, 10.25), "chrome", faces=no("down")),
            B("RodR", (10.75, 15, 9.5), (11.5, 24, 10.25), "chrome", faces=no("down")),
            B("Bar", (4.5, 24, 9.25), (11.5, 25, 10.5), "darkplastic"),
            B("Wheel0", (3.5, 0, 9.5), (5, 1, 11), "rubber"), B("Wheel1", (11, 0, 9.5), (12.5, 1, 11), "rubber"),
            B("Wheel2", (3.5, 0, 5), (5, 1, 6.5), "rubber"), B("Wheel3", (11, 0, 5), (12.5, 1, 6.5), "rubber"),
            B("Tag", (8, 11, 4.85), (10, 13.5, 5), "r4-tag", faces=("north", "south"))]


def sofa(part):
    """(round 4) Half of a first-class lounge sofa, the sitter facing north: cognac leather, a plinth on chrome feet, a deep
    seat cushion and a back cushion leaning on the padded back, the arm at the outer end (left: the arm east, right: west)."""
    els = [B("Plinth", (0, 1.5, 3), (16, 4, 15.5), "black", faces=no("up")),
           B("Seat", (0, 4, 2), (16, 8.5, 13), {"top": "r4-cognac", "all": "r4-cognac"}),
           B("SeatSeam", (7.85, 8.5, 2.5), (8.15, 8.6, 12.5), "black", faces=("up",)),
           B("Back", (0, 4, 13), (16, 18, 16), "r4-cognac"),
           B("BackPiping", (0, 18, 13.25), (16, 18.5, 15.75), "black", faces=no("down"))]
    els += P.turned([B("BackCushion", (0.25, 8.5, 10.5), (15.75, 17, 13), "r4-cognac")], rx=-8, origin=(8, 8.5, 13))
    for i, (x, z) in enumerate(((1, 3.5), (14, 3.5), (1, 13.5), (14, 13.5))):
        els.append(B(f"Foot{i}", (x, 0, z), (x + 1, 1.5, z + 1), "chrome", faces=no("down")))
    arm = [B("Arm", (13, 4, 2), (16, 12.5, 16), "r4-cognac"),
           B("ArmRoll", (13.25, 12.5, 2.25), (15.75, 13.25, 15.75), "r4-cognac", faces=no("down"))]
    return els + (arm if part == "left" else P.mirror_x(arm))


def coffee():
    """A cafe's back counter with the espresso machine on it, its group heads toward the customers (north)."""
    wood = {"front": "r4-woodv", "side": "r4-woodv", "back": "r4-woodv", "top": "worktop", "bottom": "r4-woodv"}
    els = [B("Plinth", (0.5, 0, 1.5), (15.5, 1, 15.5), "black", faces=no("down", "up")),
           B("Counter", (0, 1, 1), (16, 14, 16), wood, faces=no("down")),
           B("Top", (0, 14, 0.5), (16, 15, 16), {"top": "worktop", "all": "steel"}),
           # the machine: body, the red enamel side panels, a drip tray, two group heads with handles, a steam wand
           B("Body", (2.5, 15, 6), (13.5, 22, 14), {"front": "steel", "side": "r4-enamel", "back": "r4-enamel", "top": "steel"}),
           B("Tray", (3, 15, 3.5), (13, 15.75, 6), {"top": "tread", "all": "steel"}),
           B("Rail", (2.5, 22, 6), (13.5, 23, 14), "chrome", faces=no("down")),
           B("Gauge", (7, 19.5, 5.5), (9, 21.5, 6), "white", faces=("north",))]
    for i, x in enumerate((4.5, 9.5)):
        els += [B(f"Group{i}", (x, 17.5, 4.5), (x + 2, 19.5, 6), "chrome"),
                B(f"Basket{i}", (x + 0.25, 16.75, 4.25), (x + 1.75, 17.5, 5.75), "black"),
                B(f"Handle{i}", (x + 0.75, 17, 1.5), (x + 1.25, 17.5, 4.25), "black", faces=no("south"))]
    els += P.turned([B("Wand", (12.5, 16, 5), (13, 20, 5.5), "chrome")], rz=-18, origin=(12.75, 20, 5.25))
    # cups warming on top, a grinder with its hopper of beans, a knock box
    for i, x in enumerate((3.5, 5.5, 7.5)):
        els.append(B(f"Cup{i}", (x, 23, 8), (x + 1.5, 24.5, 9.5), "white", faces=no("down")))
    els += [B("GrinderBase", (14, 15, 9), (15.75, 19, 12.5), "black"),
            B("Hopper", (13.75, 19, 9.25), (16, 23, 12.25), "r4-beans"),
            B("HopperLid", (14, 23, 9.5), (15.75, 23.75, 12), "black", faces=no("down")),
            B("Knock", (0.5, 15, 9), (2.25, 17, 12), "black", faces=no("down"))]
    return els


def pastry():
    """A cafe's front counter: a wood-fronted base, a glass case of cakes on two tiers, a steel top; customers north."""
    els = [B("Plinth", (0.5, 0, 1.5), (15.5, 1, 15.5), "black", faces=no("down", "up")),
           B("Base", (0, 1, 1), (16, 9, 16), {"front": "r4-woodv", "side": "r4-woodv", "back": "laminate-side", "top": "steel"}),
           B("Floor", (0.5, 9, 1.5), (15.5, 9.5, 15.5), "white", faces=("up", "north")),
           B("Shelf", (0.5, 12.5, 4), (15.5, 13, 14.5), "chrome", faces=no()),
           B("Top", (0, 16.5, 1.5), (16, 17.25, 16), {"top": "worktop", "all": "steel"}),
           B("PostL", (0, 9, 1.5), (0.75, 16.5, 2.25), "chrome", faces=no("up", "down")),
           B("PostR", (15.25, 9, 1.5), (16, 16.5, 2.25), "chrome", faces=no("up", "down")),
           B("Back", (0.5, 9.5, 15.25), (15.5, 16.5, 15.75), "darksteel", faces=("north",))]
    els.append(P.transparent(B("Glass", (0.75, 9.5, 1.75), (15.25, 16.5, 2.25), "r4-glass", faces=("north", "south"))))
    els.append(P.glow([B("Light", (1, 16, 3), (15, 16.5, 14), "r4-led", faces=("down",))], 160)[0])
    rng = random.Random(3601)
    for tier, y in enumerate((9.5, 13)):
        x = 1.25
        k = 0
        while x < 13.5:
            w = rng.choice((2.5, 3, 3.5))
            h = rng.choice((1.5, 2, 2.5))
            c = rng.randrange(4)
            els.append(B(f"Cake{tier}{k}", (x, y, 6 + rng.random()), (x + w, y + h, 10.5), f"r4-cake{c}", faces=no("down")))
            x += w + 0.75
            k += 1
    return els


def till():
    """A shop's till counter, the clerk to the south: laminate body, the register's screen toward the clerk, a card
    reader toward the customer (north), carrier bags hung at the end."""
    lam = {"front": "laminate", "side": "laminate-side", "back": "laminate-side", "top": "worktop", "bottom": "laminate-side"}
    els = [B("Plinth", (0.5, 0, 1.5), (15.5, 1, 15.5), "black", faces=no("down", "up")),
           B("Body", (0, 1, 1), (16, 14, 16), lam, faces=no("down")),
           B("Top", (-0.25, 14, 0.5), (16.25, 15, 16.25), {"top": "worktop", "all": "steel"}),
           B("Drawer", (3, 15, 7), (12, 16.5, 13), "darkplastic"),
           B("Keys", (4, 16.5, 10), (11, 17, 12.5), "black", faces=no("down")),
           B("Stalk", (7, 16.5, 8), (8, 19, 9), "darkplastic", faces=no("up", "down")),
           B("Screen", (4, 19, 7.75), (11, 24, 8.75), "darkplastic"),
           B("Reader", (12.5, 15, 3), (14.5, 16, 6), "darkplastic"),
           B("ReaderTop", (12.75, 16, 3.5), (14.25, 18.5, 4.25), "darkplastic", faces=no("down")),
           B("Receipt", (5, 15, 3), (8, 15.5, 6), "white", faces=no("down"))]
    P.pic(els[6], "south", "r4-tillscreen", glow=120)
    els += P.turned([B("Bag", (14.5, 4, 2), (16.5, 12, 8), "white", faces=no("down"))], ry=-6, origin=(16, 12, 5))
    return els


def stool():
    els = [B("Base", (4, 0, 4), (12, 0.75, 12), "chrome", faces=no("down")),
           B("Post", (7.25, 0.75, 7.25), (8.75, 11, 8.75), "chrome", faces=no("up", "down")),
           B("Ring", (4.5, 5, 4.5), (11.5, 5.5, 11.5), "chrome", faces=no()),
           B("RingHole", (5, 4.9, 5), (11, 5.6, 11), "black", faces=("up", "down"))]
    els += P.octagon("Seat", 8, 8, 4.25, 11, 12.75, {"top": "r4-redvinyl", "side": "r4-redvinyl", "bottom": "black"})
    els += P.octagon("SeatRim", 8, 8, 4.4, 10.5, 11.25, "chrome", step=0.03)
    return els


def trolley():
    """An airport luggage trolley, the handle at the south: a frame on four castors, a tread deck, a basket, a handle bar
    with its brake grip, a bag fallen across it now and then (not here: the bags are their own blocks)."""
    els = [B("Deck", (3, 2.5, 0.5), (13, 3.25, 13), {"top": "tread", "all": "steel"}),
           B("Nose", (3, 2.5, 0), (13, 5, 0.75), "steel"),
           B("RailL", (2.5, 2.5, 0.5), (3, 3.25, 15), "chrome"),
           B("RailR", (13, 2.5, 0.5), (13.5, 3.25, 15), "chrome")]
    for i, (x, z) in enumerate(((3.5, 1.5), (11.5, 1.5), (3.5, 12.5), (11.5, 12.5))):
        els += [B(f"Fork{i}", (x - 0.25, 1, z - 0.5), (x + 1.25, 2.5, z + 0.5), "darksteel"),
                B(f"Wheel{i}", (x, 0, z - 1), (x + 1, 2, z + 1), "rubber")]
    # the back frame rising to the handle, leaning back a little; the basket on it
    up = [B("PostL", (2.5, 3, 14), (3.25, 17, 14.75), "chrome"),
          B("PostR", (12.75, 3, 14), (13.5, 17, 14.75), "chrome"),
          B("Bar", (2, 17, 13.75), (14, 18, 15), "chrome"),
          B("Grip", (4, 16, 14.5), (12, 16.5, 16), "black"),
          B("BasketBack", (3.25, 10, 14.1), (12.75, 14, 14.6), "r4-wire", faces=("north", "south")),
          B("BasketFloor", (3.25, 10, 11), (12.75, 10.5, 14.1), "r4-wire", faces=("up", "down")),
          B("BasketFront", (3.25, 10, 10.75), (12.75, 13, 11.25), "r4-wire", faces=("north", "south")),
          B("BasketL", (3.25, 10, 11), (3.75, 13, 14.1), "r4-wire", faces=("east", "west")),
          B("BasketR", (12.25, 10, 11), (12.75, 13, 14.1), "r4-wire", faces=("east", "west")),
          B("Sign", (5, 5, 14.6), (11, 9, 15), "r3-blue", faces=("south", "north"))]
    els += P.turned(up, rx=-8, origin=(8, 3, 14.5))
    return els


# ======================================================================== Block types

def cube_block(code, groups, textures, comment, extra=None):
    import gen_36_surfaces as GS
    data = {"variantgroups": groups, "texturesByType" if groups else "textures": textures, "blockmaterial": "Stone",
            "drawtype": "cube", "lightAbsorption": 99, "resistance": 6, "sounds": GS.STONE, "attributes": dict(GS.STRUCT)}
    if not groups:
        data.pop("variantgroups")
    data.update(extra or {})
    GS.block(code, comment, data)


def blocks():
    STRUCT = {"attributes": {"l36structure": True}}
    full = [(0, 0, 0, 1, 1, 1)]
    P.block("l36-frame", [("q", ("ee", "oe", "eo", "oo"))], lambda v: frame(v["q"]),
            "Level 36 (round 4): the space-frame ceiling: a dark acoustic deck with white tubes hung under it, square on square "
            "2 x 2 blocks a module (q: the block's x and z parity, even or odd), its top nodes on the even corners, its bottom "
            "nodes on the odd ones; a ceiling block", boxes=full, rot="none", material="Metal", sounds=P.METAL, data=STRUCT)
    P.block("l36-framelight", [("q", ("ee", "oe", "eo", "oo")), ("state", ("on", "high", "lit", "off"))],
            lambda v: framelight(v["q"], v["state"]),
            "Level 36 (round 4): a space-frame ceiling block with a linear pendant light hung from it (on: gives light; high: "
            "brighter, for the tall halls; lit: looks on, gives none; off: dead)", boxes=full, rot="none", material="Metal",
            sounds=P.METAL, data={"attributes": {"l36structure": True}, "lightHsvByType": {"*-on": [8, 1, 18], "*-high": [8, 1, 20]}})
    P.block("l36-framesky", [("q", ("ee", "oe", "eo", "oo"))], lambda v: framesky(v["q"]),
            "Level 36 (round 4): a space-frame ceiling block whose deck is a roof light (overcast sky, glowing)",
            boxes=full, rot="none", material="Glass", sounds=P.GLASS, data={"attributes": {"l36structure": True}, "lightHsv": [5, 1, 13]})
    for code, fn, what in (("l36-colfoot", colfoot, "a stainless plinth at its foot"), ("l36-colhead", colhead, "a stepped capital flaring into the ceiling")):
        P.block(code, [("quad", ("nw", "ne", "sw", "se"))], lambda v, fn=fn: fn(v["quad"]),
                f"Level 36 (round 4): a 2 x 2 column's clad block with {what} on its two outer faces (quad: the block's corner "
                "of the column)", boxes=full, rot="none", material="Metal", sounds=P.METAL, data=STRUCT)
    P.block("l36-bridge", [("part", ("lower", "glass", "upper")), ("side", SIDES)], lambda v: bridge(v["part"]),
            "Level 36 (round 4): a jet bridge's wall, the bridge to <side>: lower (corrugated panel, a handrail on brackets, a "
            "rubber skirting), glass (the glazed band, the apron and the plane's flank beyond), upper (panel, an LED cove)",
            boxes=full, material="Metal", sounds=P.METAL,
            data={"attributes": {"l36structure": True}, "lightHsvByType": {"*-upper-*": [8, 1, 9]}})
    P.block("l36-gallery", [("part", ("lip", "glass")), ("side", SIDES)], lambda v: gallery(v["part"]),
            "Level 36 (round 4): the gallery round the tall halls, on the wall toward <side>: lip (a slab edge standing out with a "
            "glass balustrade and a handrail), glass (the upper level's dark glazing behind mullions: nobody gets up there)",
            boxes=[(0, 0, 0, 1, 1, 1)], material="Metal", sounds=P.METAL, data={"attributes": {"l36structure": True}})
    P.block("l36-prayermat", [("kind", ("laid", "rolled")), ("side", SIDES)], lambda v: prayermat(v["kind"]),
            "Level 36 (round 4): a prayer mat in the prayer room, laid toward the back wall or rolled at a row's end",
            boxes=None, sel=lambda v: [(0.15, 0, 0, 0.85, 0.05, 1)] if v["kind"] == "laid" else [(0.4, 0, 0.15, 0.6, 0.2, 0.85)],
            material="Cloth", sounds=P.CLOTH)
    P.block("l36-infopylon", [("side", SIDES)], lambda v: infopylon(),
            "Level 36 (round 4): an information pylon, its lit yellow \"i\" on top, a touch screen that answers every question with "
            "the same map", boxes=[(0.3, 0, 0.35, 0.7, 1.9, 0.65)], material="Metal", sounds=P.METAL)
    P.block("l36-luggage", [("kind", ("spin0", "spin1", "duffel", "garment", "upright")), ("side", SIDES)], lambda v: luggage(v["kind"]),
            "Level 36 (round 4): luggage nobody came for, on a carousel's belt or the floor: hard-shell spinners on their side, "
            "a canvas duffel, a folded garment bag, a spinner standing with its handle out (nothing in them: the cases you can "
            "open are the mod's own suitcases)", boxes=lambda v: [(0.1, 0, 0.1, 0.9, 0.95 if v["kind"] == "upright" else 0.45, 0.9)],
            material="Cloth", sounds=P.CLOTH)
    P.block("l36-sofa", [("part", ("left", "right")), ("side", SIDES)], lambda v: sofa(v["part"]),
            "Level 36 (round 4): half of a first-class lounge sofa in cognac leather (left / right as Level 3999's couch halves)",
            boxes=[(0, 0, 0.12, 1, 0.53, 1), (0, 0, 0.8, 1, 1.1, 1)], sel=[(0, 0, 0.12, 1, 1.15, 1)], material="Cloth", sounds=P.CLOTH)
    P.block("l36-magrack", [("side", SIDES)], lambda v: magrack(),
            "Level 36 (round 4): a newsstand's magazine rack, four sloping tiers of covers (every one of them the same week's)",
            boxes=[(0, 0, 0.25, 1, 1.6, 1)], material="Metal", sounds=P.METAL)
    P.block("l36-firecab", [("side", SIDES)], lambda v: firecab(),
            "Level 36 (round 4): a fire cabinet recessed in a hall's travertine dado (the wall cube): a red extinguisher "
            "behind a glass door, its label over it", boxes=[(0, 0, 0, 1, 1, 1)], material="Stone", sounds=P.STONE,
            data={"attributes": {"l36structure": True}})
    P.block("l36-coffee", [("side", SIDES)], lambda v: coffee(),
            "Level 36 (round 4): a cafe's back counter and its espresso machine (red enamel, two group heads, a steam wand, "
            "cups warming on top), a grinder full of beans; the machine is cold", boxes=[(0, 0, 0.06, 1, 0.94, 1)],
            sel=[(0, 0, 0.06, 1, 1.5, 1)], material="Metal", sounds=P.METAL)
    P.block("l36-pastry", [("side", SIDES)], lambda v: pastry(),
            "Level 36 (round 4): a cafe's front counter, a lit glass case of cakes and pastries on it (they have not gone "
            "stale; they have not changed at all)", boxes=[(0, 0, 0.06, 1, 1.08, 1)], material="Glass", sounds=P.GLASS,
            data={"lightHsv": [8, 1, 7]})
    P.block("l36-till", [("side", SIDES)], lambda v: till(),
            "Level 36 (round 4): a shop's till counter: the register, its screen toward the clerk, a card reader, carrier bags",
            boxes=[(0, 0, 0.03, 1, 0.94, 1)], sel=[(0, 0, 0.03, 1, 1.5, 1)], material="Wood", sounds=P.WOOD)
    P.block("l36-stool", [], lambda v: stool(), "Level 36 (round 4): a chrome bar stool with a round red vinyl seat",
            boxes=[(0.25, 0, 0.25, 0.75, 0.8, 0.75)], rot="none", material="Metal", sounds=P.METAL)
    P.block("l36-trolley", [("side", SIDES)], lambda v: trolley(),
            "Level 36 (round 4): an airport luggage trolley (castors, a tread deck, a wire basket, the handle bar); side = "
            "the way it points (the handle behind)", boxes=[(0.15, 0, 0, 0.85, 0.6, 1)], sel=[(0.15, 0, 0, 0.85, 1.15, 1)],
            material="Metal", sounds=P.METAL)
    tex = lambda n: {"base": "backrooms:block/36/props/" + n}
    cube_block("l36-canopy", [{"code": "kind", "states": ["plain", "lit"]}],
               {"*-plain": {"all": {"base": "backrooms:block/36/l36-wall-purple"}, "down": tex("r4-canopyplain")},
                "*-lit": {"all": {"base": "backrooms:block/36/l36-wall-purple"}, "down": tex("r4-canopy")}},
               "Level 36 (round 4): a Travel Agency kiosk's canopy, purple gloss (plain), a downlight in its soffit every other block (lit)",
               extra={"lightHsvByType": {"*-lit": [8, 2, 11]}, "lightAbsorption": 0})
    cube_block("l36-bridgefloor", [], {"all": tex("r4-bridgefloor")},
               "Level 36 (round 4): a jet bridge's studded rubber floor", extra={"sounds": P.CLOTH})
    cube_block("l36-bridgeceil", [], {"all": tex("r4-bridgeceil")},
               "Level 36 (round 4): a jet bridge's ribbed ceiling with its light", extra={"lightHsv": [8, 1, 10], "vertexFlags": {"glowLevel": 60}})


NAMES = {
    "block-l36-frame-*": "Space-frame Ceiling",
    "block-l36-framelight-*": "Space-frame Light",
    "block-l36-framesky-*": "Space-frame Roof Light",
    "block-l36-colfoot-*": "Column Plinth",
    "block-l36-colhead-*": "Column Capital",
    "block-l36-bridge-*": "Jet Bridge Wall",
    "block-l36-bridgefloor": "Jet Bridge Floor",
    "block-l36-canopy-*": "Kiosk Canopy",
    "block-l36-bridgeceil": "Jet Bridge Ceiling",
    "block-l36-gallery-*": "Upper Gallery",
    "block-l36-magrack-*": "Magazine Rack",
    "block-l36-sofa-*": "Lounge Sofa",
    "block-l36-luggage-*": "Unclaimed Luggage",
    "block-l36-prayermat-*": "Prayer Mat",
    "block-l36-infopylon-*": "Information Pylon",
    "block-l36-firecab-*": "Fire Cabinet",
    "block-l36-coffee-*": "Espresso Counter",
    "block-l36-pastry-*": "Pastry Case",
    "block-l36-till-*": "Till Counter",
    "block-l36-stool": "Bar Stool",
    "block-l36-trolley-*": "Luggage Trolley",
}


def main():
    P.CODES.clear()
    P.SHAPE_FILES.clear()
    textures()
    blocks()
    print(f"gen_36_r4: {len(P.CODES)} block types, {len(P.SHAPE_FILES)} shapes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
