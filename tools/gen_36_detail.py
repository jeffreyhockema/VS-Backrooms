"""Level 36 "Airport" (experimental): round 3's detail blocks (2026-11-01), the multi-block pictures and the new props.

Surfaces (textures in textures/block/36/, cube or faced-cube blocks):
    l36-art-{piece}-{side}          a panel wall cube whose <side> face is one piece of a wall picture (WorldLayout.L36Art):
                                    dep / arr (a 4 x 2 DEPARTURES / ARRIVALS board), p0..p7 (1 x 2 posters: the Backrooms
                                    Travel Agency's purple ones, invented ads, notices), m0..m3 (a 2 x 1 menu board over a
                                    food stall), welc (a 4 x 1 WELCOME banner); piece "<kind>-<col>-<row>", col 0 the
                                    leftmost seen from in front, row 0 the lowest; lit
    l36-apron-{piece}-{side}        the window wall round a jet-bridge door painted as one picture, 9 x 5 (piece "c-r"):
                                    the runway view with the jet bridge running out to a parked airliner's nose; glass, lit
    l36-colposter-{n}-{row}         a column-clad cube with a poster (p0, p3, p5, p6) on all four sides (columns)
    l36-meetbox-{quad}-{row}        the meeting-point sign: a 2 x 2 x 2 lit cube over the Meeting Place (quad nw ne sw se;
                                    row lower upper), its picture on the four outer faces
    l36-finish-{kind}               coffer (a coffered ceiling), wood (oak slat ceiling), stone (travertine dado),
                                    stonetop (its top course under a steel trim); skylight (overcast sky through a grid
                                    of mullions, glowing)
Props (textures in textures/block/36/props/, JSON models facing north):
    l36-meetpost-{part}-{quad}      the meeting-point sign's post, a quarter in each of the four blocks (part base pole)
    l36-charger                     a charging post: a slim column of sockets and USB ports between the seats
    l36-payphone-{side}             a payphone under its hood, on a short counter
    l36-atm-{side}                  a cash machine in its surround
    l36-fountain-{side}             a stainless drinking fountain (Almond Water, as the coolers: BackroomsDispenser)
    l36-shoeshine-{side}            a shoe-shine chair, raised on its platform, foot rests in front
    l36-stall-{part}-{side}         part lower upper: a toilet cubicle (the bowl, partitions either side, the door ajar)

Run (from the repo root, under the asset lock): bash tools/locked.sh run python tools/gen_36_detail.py  (gen_36.py runs it)
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matlib as M  # noqa: E402
import gen_36_surfaces as GS  # noqa: E402
import gen_36_surfaces_signs as G  # noqa: E402
import gen_36_surfaces_tex as T  # noqa: E402
import gen_36_props as P  # noqa: E402
import gen_36_props_tex as TX  # noqa: E402

SIDES = GS.SIDES
K = 4
PURPLE = (92, 44, 142)
NAVYBOARD = (12, 18, 40)

# ======================================================================== The wall pictures (as WorldLayout.L36Art)

# kind: (cols, rows); kinds are numbered in this order (the layout's Depth on a wall tile)
ART = [("dep", 4, 2), ("arr", 4, 2)] + [(f"p{i}", 1, 2) for i in range(8)] + [(f"m{i}", 2, 1) for i in range(4)] + [("welc", 4, 1)]
PX = 64   # a block of picture


def _ground(colour, w, h, seed, lit=8):
    img = M.noise_hv(colour, 2, seed, (w, h), 3, (16, 8) if min(w, h) < 64 else (32, 16), hue=1.0)
    a = T.to_array(img)
    yy, xx = np.mgrid[0:h, 0:w]
    a[..., :3] += (lit * np.exp(-((yy - h / 2) / (h / 1.8)) ** 2))[..., None]
    return T.from_array(a)


def _frame(img, col=(150, 154, 160), w=3):
    a = T.to_array(img)
    H, W = a.shape[:2]
    f = np.array(col)
    a[0:w, :, :3] = f
    a[H - w:H, :, :3] = f - 30
    a[:, 0:w, :3] = f - 10
    a[:, W - w:W, :3] = f - 20
    a[0, :, :3] = f + 40
    return T.from_array(a)


def _text(img, s, spec, box, px, colour, align="centre", tracking=0):
    size = (img.width * K, img.height * K)
    m, _ = G.text_mask(size, s, spec, tuple(v * K for v in box), px * K * 1.35, align=align, min_px=4 * K, tracking=tracking)
    small = G.shrink(G.layer_from(m, colour), img.size)
    img.alpha_composite(small)
    return img


def _led(a, s, x, y, col, scale=1):
    return G._led_text(a, s, x, y, col, scale)


DEP_ROWS = [("LA 4471", "LV10", "C14", "1,204", "BOARDING"), ("LA 0088", "LV37", "A03", "48,881", "ON TIME"),
            ("LA 7720", "LV9", "B07", "906", "GATE OPEN"), ("LA 1309", "LV188", "E22", "--", "DELAYED"),
            ("LA 5502", "LV11", "D41", "73,310", "ON TIME"), ("LA 0021", "LV3999", "F09", "0", "CLOSED"),
            ("LA 6128", "LV188", "K17", "17,250", "ON TIME"), ("1784XBA8JLP", "LV186", "C32", "94,612,753", "DELAYED")]
ARR_ROWS = [("LA 3301", "LV11", "3", "ON BELT"), ("LA 4806", "LV9", "7", "ON BELT"), ("LA 1919", "LV37", "12", "LANDED"),
            ("LA 2468", "LV10", "5", "ON BELT"), ("LA 7077", "LV3999", "--", "EXPECTED"), ("LA 9184", "LV188", "21", "ON BELT"),
            ("LA 0004", "LV0", "--", "NOT KNOWN"), ("LA 6610", "LV9", "9", "ON BELT")]
STAT = {"BOARDING": (90, 232, 120), "GATE OPEN": (255, 214, 60), "DELAYED": (255, 84, 56), "CLOSED": (150, 150, 150),
        "ON BELT": (90, 232, 120), "LANDED": (232, 234, 228), "NOT KNOWN": (255, 84, 56)}


def board(kind):
    """A big flight board, 4 x 2 blocks: a navy case, the header, eight rows of amber dot-matrix text."""
    W, H = PX * 4, PX * 2
    a = np.zeros((H, W, 3))
    a[:] = (8, 9, 13)
    yy, xx = np.mgrid[0:H, 0:W]
    a[(yy % 2 == 1) | (xx % 2 == 1)] = (5, 6, 8)
    a[0:22] = NAVYBOARD
    amber, white = (255, 178, 46), (232, 234, 228)
    if kind == "dep":
        cols, heads, rows = (4, 76, 118, 142, 206), ("FLIGHT", "TO", "GATE", "COUNT", "REMARKS"), DEP_ROWS
    else:
        cols, heads, rows = (4, 72, 128, 170), ("FLIGHT", "FROM", "BELT", "REMARKS"), ARR_ROWS
    for x, h in zip(cols, heads):
        _led(a, h, x, 26, (150, 170, 220))
    for i, row in enumerate(rows):
        y = 37 + i * 11
        for j, (x, v) in enumerate(zip(cols, row)):
            col = STAT.get(v, amber if j < 2 else white)
            _led(a, v, x, y, col)
    lit = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB").filter(ImageFilter.GaussianBlur(1.1))
    a = np.maximum(a, np.asarray(lit).astype(float) * 0.5)
    img = T.from_array(a)
    title = "DEPARTURES" if kind == "dep" else "ARRIVALS"
    _text(img, title, G.DIN, (34, 2, 150, 20), 14, (246, 246, 240), align="left", tracking=K)
    _text(img, "DEPARTS  PARTENZE  SALIDAS" if kind == "dep" else "ARRIVEES  ANKUNFT  LLEGADAS", G.DIN_COND,
          (156, 5, 250, 17), 7, (150, 170, 220), align="right")
    m = Image.new("L", (W * K, H * K), 0)
    if kind == "dep":
        G.pict_plane(ImageDraw.Draw(m), (8 * K, 2 * K, 28 * K, 20 * K))
    else:
        G.pict_suitcase(ImageDraw.Draw(m), (8 * K, 2 * K, 28 * K, 20 * K))
    img.alpha_composite(G.shrink(G.layer_from(m, (255, 200, 20)), img.size))
    return _frame(img, (60, 62, 68), 2)


POSTERS = {
    # n: (background, title, body, foot, colours)
    0: ("bta", "EVERY LEVEL\nIS ONE FLIGHT\nAWAY", "Backrooms\nTravel Agency", "ASK AT BOOTH 0"),
    1: ("bta", "REMEMBER\nTO EAT", "The machines are free.\nThe tables are not\nsafe.", "BACKROOMS TRAVEL AGENCY"),
    2: ("bta", "THE CLOCKS\nHAVE STOPPED", "This is normal.\nDo not wait for\nmorning.", "BACKROOMS TRAVEL AGENCY"),
    3: ("perfume", "MAISON\nVEAU", "eau de rien", "DUTY FREE"),
    4: ("fashion", "LOSTWEAR", "wear it\nanywhere.\nyou will.", "AIRSIDE"),
    5: ("tech", "VOLTA", "stay\nconnected\n(hourly)", "CHARGERS  CABLES"),
    6: ("notice", "UNATTENDED\nBAGGAGE", "Bags left on a belt\nten rounds go to\nLost and Found.", "DO NOT LEAVE BAGS"),
    7: ("paper", "DON'T TRUST\nTHE EXIT\nSIGNS", "EMPTY SIGN\n= NO GOOD", "- a friend"),
}


def poster(n):
    """A backlit poster, 1 x 2 blocks (64 x 128): its case, the print."""
    kind, title, body, foot = POSTERS[n]
    W, H = PX, PX * 2
    if kind == "bta":
        img = _ground(PURPLE, W, H, T.seed_of(f"poster{n}"), 10)
        lay = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
        m = Image.new("L", lay.size, 0)
        G.pict_plane(ImageDraw.Draw(m), (18 * K, 8 * K, 46 * K, 36 * K))
        img.alpha_composite(G.shrink(G.layer_from(m, (255, 255, 255)), img.size))
        _text(img, title, G.DIN, (6, 40, 58, 78), 9, (255, 255, 255))
        _text(img, body, G.DIN_SEMI, (6, 82, 58, 106), 6, (226, 210, 246))
        a = T.to_array(img)
        a[110:124, 4:60, :3] = (255, 255, 255)
        img = T.from_array(a)
        _text(img, foot, G.DIN_COND, (6, 111, 58, 123), 5, PURPLE)
    elif kind == "notice":
        img = _ground((236, 238, 236), W, H, T.seed_of(f"poster{n}"), 4)
        a = T.to_array(img)
        a[6:30, 4:60, :3] = (214, 40, 46)
        img = T.from_array(a)
        _text(img, title, G.DIN, (6, 8, 58, 28), 7, (255, 255, 255))
        m = Image.new("L", (W * K, H * K), 0)
        G.pict_suitcase(ImageDraw.Draw(m), (20 * K, 36 * K, 44 * K, 60 * K))
        img.alpha_composite(G.shrink(G.layer_from(m, (40, 42, 47)), img.size))
        _text(img, body, G.DIN_SEMI, (6, 66, 58, 104), 6, (40, 42, 47))
        _text(img, foot, G.DIN_COND, (6, 108, 58, 122), 6, (214, 40, 46))
    elif kind == "paper":
        # a sheet of paper taped to the wall, marker on it
        img = T.panel_img(T.seed_of("posterpanel"), size=T.S).resize((W, H), Image.NEAREST)
        sheet = _ground((234, 230, 216), 48, 72, T.seed_of("paper"), 2)
        img.alpha_composite(sheet, (7, 30))
        d = ImageDraw.Draw(img)
        for x, y in ((9, 28), (47, 28), (9, 98), (47, 98)):
            d.rectangle((x, y, x + 7, y + 4), fill=(222, 214, 170, 200))
        _text(img, title, (["segoepr.ttf", "comicbd.ttf", "arialbd.ttf"], None), (10, 34, 54, 70), 8, (24, 24, 30))
        _text(img, body, (["segoepr.ttf", "comicbd.ttf", "arialbd.ttf"], None), (10, 72, 54, 92), 6, (190, 30, 30))
        _text(img, foot, (["segoepr.ttf", "comic.ttf", "arial.ttf"], None), (24, 92, 54, 100), 4, (24, 24, 30))
        return img
    else:
        name, bg, ink, names, var, accent = G.FASCIA[kind]
        img = _ground(bg, W, H, T.seed_of(f"poster{n}"), 8)
        if kind == "perfume":   # a tall bottle
            d = ImageDraw.Draw(img)
            d.rounded_rectangle((22, 48, 42, 92), radius=4, fill=(216, 182, 112, 200))
            d.rectangle((28, 40, 36, 48), fill=(200, 200, 204, 255))
            d.rectangle((26, 34, 38, 40), fill=(30, 30, 34, 255))
        if kind == "tech":
            m = Image.new("L", (W * K, H * K), 0)
            ImageDraw.Draw(m).polygon([(c[0] * K, c[1] * K) for c in ((38, 40), (22, 66), (31, 66), (26, 90), (44, 60), (34, 60), (40, 40))], fill=255)
            img.alpha_composite(G.shrink(G.layer_from(m, accent), img.size))
        if kind == "fashion":
            d = ImageDraw.Draw(img)
            d.rectangle((18, 40, 46, 96), fill=(214, 40, 46, 255))
            d.polygon([(18, 40), (32, 52), (46, 40)], fill=(240, 240, 238, 255))
        _text(img, title, (names, var), (4, 6, 60, 32), 10, ink)
        _text(img, body, (names, var), (4, 96, 60, 114), 5, ink)
        _text(img, foot, G.DIN_COND, (4, 116, 60, 124), 4, accent or ink)
    return _frame(img, (176, 180, 186), 2)


MENUS = {
    0: ("TERMINAL BREW", (58, 36, 26), (238, 220, 190), [("ESPRESSO", "2.80"), ("FLAT WHITE", "3.60"), ("TEA", "2.40"), ("MUFFIN", "3.10")]),
    1: ("NOODLE GATE", (160, 24, 30), (255, 236, 200), [("RAMEN", "9.50"), ("UDON", "8.90"), ("GYOZA x6", "5.20"), ("MISO", "2.50")]),
    2: ("BURGER BAY", (24, 26, 30), (250, 200, 40), [("CLASSIC", "8.40"), ("DOUBLE", "10.90"), ("FRIES", "3.20"), ("SHAKE", "4.50")]),
    3: ("SLICE", (34, 82, 44), (250, 246, 230), [("MARGHERITA", "4.20"), ("PEPPERONI", "4.80"), ("GARLIC KNOTS", "3.60"), ("SODA", "2.20")]),
}


def menu(n):
    name, bg, ink, items = MENUS[n]
    W, H = PX * 2, PX
    img = _ground(bg, W, H, T.seed_of(f"menu{n}"), 9)
    _text(img, name, G.DIN, (6, 3, 122, 16), 9, ink)
    a = T.to_array(img)
    a[18, 8:120, :3] = ink
    img = T.from_array(a)
    for i, (item, price) in enumerate(items):
        y = 22 + i * 10
        _text(img, item, G.DIN_SEMI, (8, y, 90, y + 9), 6, ink, align="left")
        _text(img, price, G.DIN_SEMI, (92, y, 120, y + 9), 6, ink, align="right")
    return _frame(img, (40, 40, 44), 2)


def welcome():
    W, H = PX * 4, PX
    img = _ground((24, 52, 110), W, H, T.seed_of("welcome"), 10)
    _text(img, "WELCOME", G.DIN, (10, 6, 246, 34), 20, (255, 255, 255), tracking=2 * K)
    _text(img, "BIENVENUE  ·  WILLKOMMEN  ·  BIENVENIDOS  ·  BENVENUTI  ·  WELKOM", G.DIN_COND, (10, 38, 246, 54), 8,
          (200, 214, 246))
    return _frame(img, (170, 174, 180), 3)


def art_pictures():
    out = {}
    for kind, cols, rows in ART:
        if kind in ("dep", "arr"):
            img = board(kind)
        elif kind == "welc":
            img = welcome()
        elif kind.startswith("p"):
            img = poster(int(kind[1:]))
        else:
            img = menu(int(kind[1:]))
        out[kind] = img
        for c in range(cols):
            for r in range(rows):
                y0 = (rows - 1 - r) * PX
                T.save(img.crop((c * PX, y0, c * PX + PX, y0 + PX)), f"l36-art-{kind}-{c}-{r}")
    return out


# ======================================================================== The plane at the gate

APRON_COLS, APRON_ROWS = 9, 5


def apron():
    """The runway view behind a jet-bridge door, 9 x 5 blocks at 64 px: the painted view (as the windows', rows sky,
    sky, horizon, mid, low from the top) and on it the airliner parked nose-in, the jet bridge running out to its door."""
    v = T.view()   # 256 x 64: sky, horizon, mid, low
    W, H = APRON_COLS * PX, APRON_ROWS * PX
    a = np.zeros((H, W, 3))
    col = np.concatenate([v[0:64], v], axis=0)   # sky again on top
    for c in range(APRON_COLS):
        a[:, c * PX:(c + 1) * PX] = col
    img = T.from_array(a)
    Kp = 4
    big = Image.new("RGBA", (W * Kp, H * Kp), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)

    def P_(x, y):
        return (x * Kp, y * Kp)

    WHITE, SHADE, NAVY = (236, 238, 240, 255), (196, 200, 206, 255), (34, 46, 98, 255)
    cx, cy, R = 420, 168, 74
    # the tail fin, far behind, over the fuselage
    d.polygon([P_(cx - 6, cy - R - 2), P_(cx + 6, cy - R - 2), P_(cx + 4, 34), P_(cx - 2, 30)], fill=NAVY)
    # the wings, seen nearly edge-on, drooping to the tips, and the engines under them
    for s in (-1, 1):
        d.polygon([P_(cx + s * 40, cy + 34), P_(cx + s * 300, cy + 14), P_(cx + s * 300, cy + 20), P_(cx + s * 40, cy + 46)],
                  fill=(206, 210, 216, 255))
        ex, ey, er = cx + s * 150, cy + 56, 34
        d.ellipse(((ex - er) * Kp, (ey - er) * Kp, (ex + er) * Kp, (ey + er) * Kp), fill=(214, 218, 224, 255))
        d.ellipse(((ex - er + 6) * Kp, (ey - er + 6) * Kp, (ex + er - 6) * Kp, (ey + er - 6) * Kp), fill=(40, 42, 48, 255))
        d.ellipse(((ex - 8) * Kp, (ey - 8) * Kp, (ex + 8) * Kp, (ey + 8) * Kp), fill=(150, 154, 160, 255))
        d.rectangle(((ex - 4) * Kp, (ey - er - 14) * Kp, (ex + 4) * Kp, (ey - er + 2) * Kp), fill=(190, 194, 200, 255))
    # the nose gear: a strut, two wheels on the apron
    d.rectangle(((cx - 4) * Kp, (cy + 60) * Kp, (cx + 4) * Kp, 288 * Kp), fill=(120, 124, 130, 255))
    for wx in (cx - 14, cx + 6):
        d.rounded_rectangle((wx * Kp, 276 * Kp, (wx + 9) * Kp, 300 * Kp), radius=3 * Kp, fill=(26, 26, 28, 255))
    # the fuselage seen nose-on: a white disc, shaded underneath, the navy cheat line, the radome
    d.ellipse(((cx - R) * Kp, (cy - R) * Kp, (cx + R) * Kp, (cy + R) * Kp), fill=WHITE)
    d.chord(((cx - R) * Kp, (cy - R) * Kp, (cx + R) * Kp, (cy + R) * Kp), 20, 160, fill=SHADE)
    d.ellipse(((cx - R * 0.55) * Kp, (cy - R * 0.25) * Kp, (cx + R * 0.55) * Kp, (cy + R * 0.85) * Kp), fill=(222, 224, 228, 255))
    # cockpit windows: a band of six dark panes across the upper third
    for i in range(6):
        u0 = -0.62 + i * 0.21
        x0, x1 = cx + u0 * R, cx + (u0 + 0.18) * R
        lift = abs(u0 + 0.09) * 10
        d.polygon([P_(x0, cy - 34 + lift), P_(x1, cy - 34 + lift + (2 if u0 > 0 else -2)), P_(x1, cy - 20 + lift * 0.6),
                   P_(x0, cy - 20 + lift * 0.6)], fill=(30, 36, 48, 255))
    d.arc(((cx - R + 2) * Kp, (cy - R + 2) * Kp, (cx + R - 2) * Kp, (cy + R - 2) * Kp), 200, 340, fill=NAVY, width=5 * Kp)
    # the jet bridge: from over the gate's door (column 4) out to the airliner's front door, on its wheeled leg
    dx0, dx1 = 4 * PX, 5 * PX
    d.polygon([P_(dx0 - 10, 150), P_(cx - 30, 160), P_(cx - 30, 192), P_(dx0 - 10, 222)], fill=(150, 154, 160, 255))
    d.polygon([P_(dx0 - 10, 150), P_(cx - 30, 160), P_(cx - 30, 166), P_(dx0 - 10, 160)], fill=(118, 122, 128, 255))
    for i in range(8):   # its corrugations and a row of small windows
        x = dx0 + i * (cx - 30 - dx0) / 8
        d.line((x * Kp, (152 + i * 1.2) * Kp, x * Kp, (220 - i * 3.6) * Kp), fill=(128, 132, 138, 255), width=Kp)
        d.rectangle(((x + 4) * Kp, (172 + i * 0.6) * Kp, (x + 10) * Kp, (178 + i * 0.4) * Kp), fill=(60, 72, 90, 255))
    d.rectangle(((cx - 34) * Kp, 156 * Kp, (cx - 22) * Kp, 196 * Kp), fill=(90, 92, 96, 255))   # the cab against the door
    lx = (dx0 + cx) / 2 + 20
    d.rectangle(((lx - 5) * Kp, 200 * Kp, (lx + 5) * Kp, 284 * Kp), fill=(110, 114, 120, 255))
    d.rectangle(((lx - 18) * Kp, 280 * Kp, (lx + 18) * Kp, 290 * Kp), fill=(70, 72, 76, 255))
    for wx in (lx - 16, lx + 6):
        d.ellipse((wx * Kp, 286 * Kp, (wx + 10) * Kp, 298 * Kp), fill=(26, 26, 28, 255))
    # the airline's name on the bridge's flank
    G_ = Image.new("L", big.size, 0)
    m, _ = G.text_mask(big.size, "LIMINAL AIR", G.DIN, ((dx0 + 30) * Kp, 180 * Kp, (cx - 60) * Kp, 196 * Kp), 9 * Kp * 1.35)
    big.alpha_composite(G.layer_from(m, (34, 46, 98)))
    small = big.resize((W, H), Image.LANCZOS)
    img.alpha_composite(small)
    a = T.to_array(img)
    # the glass and the mullions at each block's left edge, as the windows'
    yy, xx = np.mgrid[0:H, 0:W]
    a[..., :3] = a[..., :3] * 0.94 + np.array((150, 166, 180)) * 0.06
    a[..., :3] += (np.exp(-((((xx + yy) % 64) - 30) / 9.0) ** 2) * 7)[..., None]
    for c in range(APRON_COLS):
        x = c * PX
        a[:, x:x + 3, :3] = (64, 68, 74)
        a[:, x, :3] = (92, 96, 102)
        a[:, x + 3, :3] *= 0.7
    img = T.from_array(a)
    for c in range(APRON_COLS):
        for r in range(APRON_ROWS):
            y0 = (APRON_ROWS - 1 - r) * PX
            T.save(img.crop((c * PX, y0, c * PX + PX, y0 + PX)), f"l36-apron-{c}-{r}")


# ======================================================================== The meeting point's sign, columns, finishes

def meetbox():
    """One face of the meeting-point cube, 2 x 2 blocks (128 x 128): white, lit, the yellow pictogram tile and the words."""
    W = PX * 2
    img = _ground((244, 244, 240), W, W, T.seed_of("meetbox"), 6)
    size = (W * K, W * K)
    lay = G.tile_layer(size, (30 * K, 10 * K, 98 * K, 78 * K), "meeting")
    img.alpha_composite(G.shrink(lay, img.size))
    _text(img, "MEETING\nPOINT", G.DIN, (8, 82, 120, 112), 13, (40, 42, 47))
    _text(img, "POINT DE RENCONTRE  ·  TREFFPUNKT", G.DIN_COND, (8, 114, 120, 122), 4, (110, 112, 118))
    img = _frame(img, (60, 62, 68), 3)
    for half, x0 in (("l", 0), ("r", PX)):
        for row, y0 in (("upper", 0), ("lower", PX)):
            T.save(img.crop((x0, y0, x0 + PX, y0 + PX)), f"l36-meet-{half}-{row}")
    T.save(_ground((60, 62, 68), 32, 32, T.seed_of("meetinner"), 0), "l36-meet-inner")


def finishes():
    s = T.seed_of("finish")
    S = T.S
    # A coffered ceiling: a deep square recess in each block, its sides lit from below, a white grid between
    cof = M.plaster(s, size=S, base=(226, 226, 222), grain=2, mottle=3, roller=0.1, bumps=0)
    a = T.to_array(cof)
    a[5:27, 5:27, :3] -= 26
    a[5:7, 5:27, :3] += 16
    a[5:27, 5:7, :3] += 8
    a[25:27, 5:27, :3] -= 12
    a[25:27, 5:27, :3] -= 6
    a[9:23, 9:23, :3] -= 8
    T.save(T.from_array(a), "l36-finish-coffer")
    wood = M.wood_planks(s + 1, size=S, base=(170, 128, 84), planks=4, direction="h", grain=3, contrast=0.8)
    a = T.to_array(wood)
    for y in range(0, S, 8):
        a[y + 6:y + 8, :, :3] = (40, 34, 30)
    T.save(T.from_array(a), "l36-finish-wood")
    st = M.noise_hv((214, 196, 166), 4, s + 2, S, 8, (16, 8))
    a = T.to_array(st)
    rng = np.random.default_rng(s)
    for _ in range(26):   # the travertine's pits and veins, running along the slab
        x, y = int(rng.integers(0, S)), int(rng.integers(0, S))
        a[y, x:x + int(rng.integers(2, 7)), :3] -= 22
    a[15, :, :3] -= 18
    a[31, :, :3] -= 26
    a[:, 0, :3] -= 18
    T.save(T.from_array(a), "l36-finish-stone")
    top = T.to_array(st).copy()
    top[0:5, :, :3] = (176, 180, 184)
    top[0, :, :3] = (210, 214, 218)
    top[4, :, :3] = (110, 114, 120)
    top[31, :, :3] -= 26
    T.save(T.from_array(top), "l36-finish-stonetop")
    sky = np.zeros((S, S, 3))
    sky[:] = (196, 202, 206)
    cl = np.array(M.fbm((S, S), s + 3, (16, 8), 0.6))
    sky += cl[..., None] * np.array((8, 8, 7))
    sky[0:2, :] = (120, 124, 130)
    sky[:, 0:2] = (120, 124, 130)
    sky[15:17, :] = (140, 144, 150)
    T.save(T.from_array(sky), "l36-finish-skylight")


# ======================================================================== Surfaces' block types

ART_LIGHT = {"dep": [36, 3, 6], "arr": [36, 3, 6], "welc": [36, 3, 5]}


def surface_blocks():
    sh = GS.faced_cube("l36-art", 140, "l36-art-dep-0-0", "l36-wall-panel")
    pieces = [f"{k}-{c}-{r}" for k, cols, rows in ART for c in range(cols) for r in range(rows)]
    GS.block("l36-art", "Level 36: a panel wall cube whose <side> face is a piece of a lit wall picture: the DEPARTURES and "
             "ARRIVALS boards (4 x 2), posters (p0-p2 the Backrooms Travel Agency's, p3-p5 invented ads, p6 the baggage "
             "notice, p7 a wanderer's sheet taped up), the food stalls' menu boards (2 x 1), the WELCOME banner (4 x 1); "
             "piece <kind>-<col>-<row>, col 0 leftmost seen from in front, row 0 lowest",
             {"variantgroups": [{"code": "piece", "states": pieces}, {"code": "side", "states": SIDES}],
              "shapeByType": GS.rotated_shapes("*", sh),
              "texturesByType": {f"l36-art-{p}-*": {"front": GS.tex("l36-art-" + p), "side": GS.tex("l36-wall-panel")} for p in pieces},
              "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]},
              "blockmaterial": "Stone", "drawtype": "json", "sidesolid": {"all": True}, "sideopaque": {"all": True},
              "lightHsvByType": {f"l36-art-{k}-*": v for k, v in ART_LIGHT.items()},
              "lightAbsorption": 0, "resistance": 6, "sounds": GS.STONE, "attributes": dict(GS.STRUCT)})

    # (round 4) with the runway windows' mullion standing proud at each block's edge
    win = GS.box("Cube", (0, 0, 0), (16, 16, 16), {"front": "front", "all": "side"})
    win["faces"]["north"]["glow"] = 70
    sh = GS.shape("l36-apron", [win, GS.box("Mullion", (0, 0, -0.75), (0.75, 16, 0), "darksteel", faces=("north", "east", "west"))],
                  {"front": "l36-apron-0-0", "side": "l36-wall-plaster"})
    pieces = [f"{c}-{r}" for c in range(APRON_COLS) for r in range(APRON_ROWS)]
    GS.block("l36-apron", "Level 36: the window wall round a jet-bridge door, painted as one picture 9 x 5 (piece <col>-<row>): "
             "the runway view, a jet bridge running out to a parked airliner's nose; unbreakable glass, lit as the windows",
             {"variantgroups": [{"code": "piece", "states": pieces}, {"code": "side", "states": SIDES}],
              "shapeByType": GS.rotated_shapes("*", sh),
              "texturesByType": {f"l36-apron-{p}-*": {"front": GS.tex("l36-apron-" + p), "side": GS.tex("l36-wall-plaster")} for p in pieces},
              "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]},
              "blockmaterial": "Glass", "drawtype": "json", "sidesolid": {"all": True}, "sideopaque": {"all": True},
              "lightHsv": [20, 1, 7], "lightAbsorption": 0, "resistance": 6, "sounds": GS.GLASS, "attributes": dict(GS.STRUCT)})

    GS.cube("l36-colposter", [{"code": "n", "states": ["p0", "p3", "p5", "p6"]}, {"code": "row", "states": ["0", "1"]}],
            {f"*-{n}-{r}": {"all": GS.tex(f"l36-art-{n}-0-{r}"), "up": GS.tex("l36-wall-column"), "down": GS.tex("l36-wall-column")}
             for n in ("p0", "p3", "p5", "p6") for r in "01"},
            "Level 36: a column with a lit poster on each of its faces (the Travel Agency's, two ads, the baggage notice)",
            by_type=True, extra={"vertexFlags": {"glowLevel": 90}})

    tex = {}
    quads = ["nw", "ne", "sw", "se"]
    for q in quads:
        qx, qz = (0 if q[1] == "w" else 1), (0 if q[0] == "n" else 1)
        for row in ("lower", "upper"):
            def face(half):
                return GS.tex(f"l36-meet-{half}-{row}")
            # (left and right as seen by someone facing that face)
            t = {"north": face("r" if qx == 0 else "l"), "south": face("l" if qx == 0 else "r"),
                 "west": face("l" if qz == 0 else "r"), "east": face("r" if qz == 0 else "l")}
            # the inner faces, toward the cube's middle, unseen: plain
            t["east" if qx == 0 else "west"] = GS.tex("l36-meet-inner")
            t["south" if qz == 0 else "north"] = GS.tex("l36-meet-inner")
            t["up"] = GS.tex("l36-meet-inner")
            t["down"] = GS.tex("l36-meet-inner")
            tex[f"*-{q}-{row}"] = t
    # (round 4) a model, not a cube: the lit faces in a brushed aluminium frame standing proud along the cube's outer edges
    shapes_, ftex = {}, {}
    for q in quads:
        ox, oz = (0 if q[1] == "w" else 16), (0 if q[0] == "n" else 16)
        for row in ("lower", "upper"):
            cube_ = GS.box("Cube", (0, 0, 0), (16, 16, 16), {f: "f" + f[0] for f in ("north", "east", "south", "west", "up", "down")})
            for f in ("north", "east", "south", "west"):
                cube_["faces"][f]["glow"] = 200
            bars = [GS.box("Edge", (ox - 0.75 if ox == 0 else 15.25, 0, oz - 0.75 if oz == 0 else 15.25),
                           (0.75 if ox == 0 else 16.75, 16, 0.75 if oz == 0 else 16.75), "alu")]
            y1, y2 = (15, 16.75) if row == "upper" else (-0.75, 1)
            bars += [GS.box("RimX", (-0.75 if ox == 0 else 0, y1, oz - 0.75 if oz == 0 else 15.25), (16 if ox == 0 else 16.75, y2, 0.75 if oz == 0 else 16.75), "alu"),
                     GS.box("RimZ", (ox - 0.75 if ox == 0 else 15.25, y1, 0), (0.75 if ox == 0 else 16.75, y2, 16), "alu")]
            shapes_[f"*-{q}-{row}"] = {"base": GS.shape(f"l36-meetbox-{q}-{row}", [cube_] + bars, {"alu": "props/r4-alu"})}
            t = tex[f"*-{q}-{row}"]
            ftex[f"*-{q}-{row}"] = {"f" + f[0]: t[f] for f in ("north", "east", "south", "west", "up", "down")}
    GS.block("l36-meetbox", "Level 36: the meeting-point sign, a lit 2 x 2 x 2 cube on a post over the Meeting Place (quad: the "
             "block's corner of it; row lower/upper): the yellow pictogram and MEETING POINT on its four faces, in an aluminium "
             "frame (round 4)",
             {"variantgroups": [{"code": "quad", "states": quads}, {"code": "row", "states": ["lower", "upper"]}],
              "shapeByType": shapes_, "texturesByType": ftex, "blockmaterial": "Glass", "drawtype": "json",
              "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightHsv": [8, 1, 12], "lightAbsorption": 0,
              "resistance": 6, "sounds": GS.GLASS, "attributes": dict(GS.STRUCT)})

    kinds = ["coffer", "wood", "stone", "stonetop", "skylight"]
    GS.cube("l36-finish", [{"code": "kind", "states": kinds}],
            {**{f"*-{k}": {"all": GS.tex("l36-finish-" + k)} for k in kinds},
             "*-stone": {"all": GS.tex("l36-finish-stone"), "up": GS.tex("l36-wall-panel"), "down": GS.tex("l36-wall-panel")},
             "*-stonetop": {"all": GS.tex("l36-finish-stonetop"), "up": GS.tex("l36-wall-panel"), "down": GS.tex("l36-wall-panel")}},
            "Level 36: round 3's finishes: coffer (a coffered ceiling), wood (oak slats), stone (a travertine dado on the "
            "walls of the public halls) and stonetop (its top course under a steel trim), skylight (overcast sky through "
            "the mullions of a roof light, glowing)", by_type=True,
            extra={"vertexFlagsByType": {"*-skylight": {"glowLevel": 120}},
                   # (round 4) daylight through the roof lights (the Meeting Place's floor was dark under its skylight)
                   "lightHsvByType": {"*-skylight": [5, 1, 13]}})


# ======================================================================== Props

def _tex_props():
    S = 32
    s = TX.seed_of("r3")
    TX.save(M.brushed_metal(s, base=(196, 200, 206), direction="v", streak=8, sheen=10), "r3-steel")
    TX.save(M.painted_metal(s + 1, base=(56, 58, 64), grain=2, mottle=3, panel=False, chips=0), "r3-dark")
    TX.save(M.painted_metal(s + 2, base=(232, 232, 228), grain=2, mottle=2, panel=False, chips=0), "r3-white")
    TX.save(M.painted_metal(s + 3, base=(30, 92, 160), grain=2, mottle=3, panel=False, chips=0), "r3-blue")
    TX.save(M.wood_planks(s + 4, size=S, base=(118, 74, 44), planks=2, direction="h", grain=3, contrast=0.8), "r3-wood")
    TX.save(M.noise_hv((120, 24, 30), 3, s + 5, S, 4, (16, 8)), "r3-leather")
    TX.save(M.noise_hv((150, 156, 150), 2, s + 6, S, 3, (16, 8)), "r3-partition")
    TX.save(M.noise_hv((244, 244, 240), 1, s + 7, S, 2, (16, 8)), "r3-porcelain")
    TX.save(M.noise_hv((10, 12, 16), 1, s + 8, S, 1, (16, 8)), "r3-black")
    for i, c in enumerate(BOTTLES):   # glass bottles: the tint, a pale highlight down one side, a label band
        img = M.noise_hv(c, 2, s + 20 + i, S, 2, (16, 8))
        d = ImageDraw.Draw(img)
        d.rectangle((4, 0, 6, 31), fill=tuple(min(255, v + 60) for v in c) + (255,))
        d.rectangle((0, 14, 31, 22), fill=(236, 232, 220, 255))
        d.rectangle((0, 0, 31, 3), fill=(40, 40, 44, 255))
        TX.save(img, f"r3-bottle{i}")
    # the charger's face: sockets and USB ports in two columns
    img = Image.new("RGBA", (S, S), (232, 232, 228, 255))
    d = ImageDraw.Draw(img)
    for y in (3, 12, 21):
        d.rectangle((4, y, 13, y + 7), fill=(210, 210, 206, 255), outline=(150, 150, 146, 255))
        d.rectangle((7, y + 2, 7, y + 4), fill=(30, 30, 30, 255))
        d.rectangle((10, y + 2, 10, y + 4), fill=(30, 30, 30, 255))
        d.rectangle((18, y, 27, y + 7), fill=(40, 40, 44, 255))
        d.rectangle((20, y + 2, 25, y + 3), fill=(30, 120, 220, 255))
        d.rectangle((20, y + 5, 25, y + 5), fill=(120, 120, 120, 255))
    d.rectangle((4, 29, 27, 30), fill=(30, 120, 220, 255))
    TX.save(img, "r3-charger")
    # screens: the ATM's (blue, CASH), the payphone's keypad
    img = Image.new("RGBA", (S, S), (20, 40, 90, 255))
    d = ImageDraw.Draw(img)
    TX.centre_text(img, "CASH", 4, (255, 255, 255))
    TX.centre_text(img, "INSERT", 14, (160, 200, 255))
    TX.centre_text(img, "CARD", 21, (160, 200, 255))
    TX.save(img, "r3-atmscreen")
    img = Image.new("RGBA", (S, S), (60, 62, 68, 255))
    d = ImageDraw.Draw(img)
    for i in range(4):
        for j in range(3):
            d.rectangle((7 + j * 7, 6 + i * 6, 11 + j * 7, 9 + i * 6), fill=(200, 202, 206, 255))
    TX.save(img, "r3-keypad")
    img = Image.new("RGBA", (S, S), (30, 92, 160, 255))
    TX.centre_text(img, "PHONE", 12, (255, 255, 255))
    TX.save(img, "r3-phonesign")
    img = Image.new("RGBA", (S, S), (30, 120, 60, 255))
    TX.centre_text(img, "ATM", 12, (255, 255, 255))
    TX.save(img, "r3-atmsign")


B = P.B
no = P.no


QUAD_CORNER = {"nw": (16, 16), "ne": (0, 16), "sw": (16, 0), "se": (0, 0)}   # the sign's middle, in the block


def _corner_box(quad, half):
    cx, cz = QUAD_CORNER[quad]
    x0, x1 = (cx - half, cx) if cx else (0, half)
    z0, z1 = (cz - half, cz) if cz else (0, half)
    return x0, z0, x1, z1


def meetpost(part, quad):
    # a quarter of an 8 px square post at the corner of the block nearest the sign's middle
    x0, z0, x1, z1 = _corner_box(quad, 4)
    els = [B("Post", (x0, 0, z0), (x1, 16, z1), "r3-dark", faces=no("down"))]
    if part == "base":
        x0, z0, x1, z1 = _corner_box(quad, 10)
        els.append(B("Plinth", (x0, 0, z0), (x1, 3, z1), "r3-steel", faces=no("down")))
    return els


def charger():
    els = [B("Base", (5, 0, 5), (11, 1, 11), "r3-steel", faces=no("down")),
           B("Column", (6, 1, 6), (10, 20, 10), {"front": "r3-charger", "back": "r3-charger", "side": "r3-charger", "top": "r3-white", "bottom": "r3-white"}),
           B("Cap", (5.5, 20, 5.5), (10.5, 21, 10.5), "r3-blue", faces=no("down"))]
    for e in els[1:2]:
        for f in ("north", "south", "east", "west"):
            e["faces"][f]["glow"] = 30
    return els


def payphone():
    """(round 4) A payphone against the wall behind it (south): a stainless hood with side cheeks and a lit PHONE header,
    the phone body (keypad, coin slot, coin return, the instruction card), the handset in its cradle on an armoured cord,
    a directory shelf with its binder, all on a post."""
    els = [B("HoodBack", (1, 9, 15), (15, 27, 16), "r3-steel", faces=("north", "up")),
           B("CheekL", (1, 9, 5), (1.75, 27, 15), "r3-steel", faces=no("down")),
           B("CheekR", (14.25, 9, 5), (15, 27, 15), "r3-steel", faces=no("down")),
           B("Roof", (1, 26, 4), (15, 27.5, 16), "r3-steel", faces=no()),
           B("Header", (1.75, 24.5, 4.25), (14.25, 26, 5), "r3-steel", faces=no("up")),
           B("Body", (4, 12.5, 12), (12, 23.5, 15), {"front": "r3-dark", "side": "r3-dark", "top": "r3-dark", "bottom": "r3-dark", "back": "r3-dark"}),
           B("Keys", (6.5, 14.5, 11.75), (10, 19, 12), "r3-keypad", faces=("north",)),
           B("CoinSlot", (9, 21, 11.6), (10.5, 22.5, 12), "r3-steel", faces=no("south")),
           B("Return", (8, 13, 11.25), (10.5, 14, 12), "r3-steel", faces=no("south")),
           B("Card", (4.5, 19.75, 11.9), (8.5, 22.75, 12), "r3-white", faces=("north",)),
           B("Cradle", (4.25, 15, 11), (5.75, 22, 12), "r3-steel", faces=no("south")),
           B("Handset", (4.3, 14.5, 10.25), (5.7, 22.5, 11), "r3-black"),
           B("Ear", (4.1, 21, 9.75), (5.9, 22.75, 10.5), "r3-black"),
           B("Mouth", (4.1, 14.25, 9.75), (5.9, 16, 10.5), "r3-black"),
           B("Cord", (5.75, 9.5, 10.5), (6.5, 14.5, 11.25), "r3-steel"),
           B("CordLoop", (6.5, 8.5, 10.5), (9, 9.25, 11.25), "r3-steel"),
           B("CordUp", (8.5, 9.75, 10.5), (9.25, 12.5, 11.25), "r3-steel"),
           B("Shelf", (1.75, 9, 3.5), (14.25, 10, 15), "r3-dark", faces=no()),
           B("ShelfLip", (1.75, 8.5, 3.25), (14.25, 10.25, 3.75), "r3-steel", faces=no("south")),
           B("Binder", (10.5, 10, 5.5), (13.5, 11.25, 10.5), "r3-blue"),
           B("Post", (7, 0, 13), (9, 9, 15), "r3-steel", faces=no("down")),
           B("Foot", (6, 0, 12), (10, 0.5, 16), "r3-dark", faces=no("down"))]
    P.pic(els[4], "north", "r3-phonesign", glow=140)
    return els


def atm():
    """(round 4) A cash machine in its dark surround: a privacy hood over an inset screen (lit) with side keys, a sloping
    keypad shelf, the card slot with its green LED, the receipt and cash slots, the lit ATM topper."""
    els = [B("Surround", (0, 0, 9), (16, 31, 16), "r3-dark", faces=no("down", "south")),
           B("Plinth", (1.5, 0, 6), (14.5, 1.5, 9), "r3-black", faces=no("down", "south")),
           B("Body", (2, 1.5, 6.5), (14, 13, 9), "r3-steel", faces=no("down", "south")),
           B("Fascia", (2, 13, 5.5), (14, 24, 9), "r3-steel", faces=no("south", "down")),
           B("Bezel", (3.5, 15, 5.25), (12.5, 22, 5.5), "r3-black", faces=("north",)),
           B("Screen", (4.5, 16, 5.1), (11.5, 21, 5.25), "r3-black", faces=("north",)),
           B("HoodTop", (2, 24, 2.5), (14, 24.75, 9), "r3-dark", faces=no("south")),
           B("HoodL", (2, 14, 2.5), (2.75, 24, 5.5), "r3-dark", faces=no("south")),
           B("HoodR", (13.25, 14, 2.5), (14, 24, 5.5), "r3-dark", faces=no("south")),
           B("CardSlot", (11, 11.25, 5.75), (13, 12.25, 6.5), "r3-black", faces=no("south")),
           B("CardLed", (11.25, 12.25, 5.85), (11.75, 12.6, 6.25), "r3-blue", faces=no("south"), glow=200),
           B("Receipt", (3, 11.5, 6.25), (6, 12, 6.5), "r3-black", faces=("north",)),
           B("Cash", (4, 4, 6.25), (12, 5.5, 6.5), "r3-black", faces=("north",)),
           B("Topper", (1, 25.5, 8), (15, 30, 9), "r3-dark", faces=no("south"))]
    for i in range(4):
        for side, x in (("L", 2.75), ("R", 12.5)):
            els.append(B(f"Key{side}{i}", (x, 16 + i * 1.5, 5.0), (x + 0.75, 16.75 + i * 1.5, 5.5), "r3-white", faces=no("south")))
    els += P.turned([B("Shelf", (3, 13, 2), (13, 13.75, 6), {"top": "r3-keypad", "side": "r3-steel", "front": "r3-steel", "bottom": "r3-steel", "back": "r3-steel"})],
                    rx=18, origin=(8, 13, 6))
    P.pic(els[5], "north", "r3-atmscreen", glow=150)
    P.pic(els[-2], "north", "r3-atmsign", glow=130)
    return els


def fountain():
    """(round 4) A stainless bi-level drinking fountain against the wall: two basins with rounded fronts on brackets, a
    bubbler and a push bar each, a bottle filler above with its lit panel, the back plate down to the floor."""
    els = [B("Back", (1, 0, 14.5), (15, 26, 16), "r3-steel", faces=("north", "up", "east", "west")),
           B("Filler", (3, 18, 12), (13, 25.5, 14.5), "r3-steel", faces=no("south")),
           B("FillerPanel", (4.5, 21.5, 11.75), (11.5, 24.5, 12), "r3-blue", faces=("north",), glow=120),
           B("FillerSpout", (7.25, 20.5, 11), (8.75, 21.5, 12.5), "r3-steel", faces=no("south")),
           B("FillerTray", (4.5, 18, 10.75), (11.5, 18.5, 12), "r3-black", faces=no("south"))]
    for name, x1, x2, y in (("Hi", 8.25, 15, 13.5), ("Lo", 1, 7.75, 10.5)):
        els += [B(f"Basin{name}", (x1, y - 2, 4.5), (x2, y, 14.5), "r3-steel", faces=no("south")),
                B(f"Nose{name}", (x1 + 0.75, y - 2.5, 3.5), (x2 - 0.75, y - 0.25, 4.5), "r3-steel", faces=no("south")),
                B(f"Bowl{name}", (x1 + 0.75, y - 0.5, 5.25), (x2 - 0.75, y + 0.05, 13.75), "r3-black", faces=("up",)),
                B(f"Bubbler{name}", ((x1 + x2) / 2 - 0.75, y, 11), ((x1 + x2) / 2 + 0.75, y + 1.5, 12.5), "r3-steel", faces=no("down")),
                B(f"Bar{name}", (x1 + 1, y - 3.25, 2.75), (x2 - 1, y - 2.5, 3.5), "r3-steel"),
                B(f"Bracket{name}", ((x1 + x2) / 2 - 1, 2, 12.5), ((x1 + x2) / 2 + 1, y - 2, 14.5), "r3-steel", faces=no("up", "south"))]
    return els


def shoeshine():
    """(round 4) A shoe-shine chair, raised on its wooden platform: a step at the front, a buttoned red leather seat and
    back on a wooden frame with brass-capped arms, two chrome shoe rests on posts, the shiner's kit box with brushes and
    tins on the platform's edge."""
    wood = "r3-wood"
    els = [B("Platform", (0, 1.5, 3), (16, 6, 16), wood),
           B("PlatformTrim", (-0.25, 5.5, 2.75), (16.25, 6.25, 16.25), "r3-steel", faces=no("down")),
           B("Step", (1, 0, 0), (15, 3, 3), {"top": "r3-steel", "all": wood}),
           B("Toe", (0.5, 0, 3), (15.5, 1.5, 15.5), "r3-black", faces=("north", "east", "west")),
           B("Base", (3, 6, 7.5), (13, 11, 14.5), wood),
           B("Seat", (2.5, 11, 6.5), (13.5, 13.5, 14.5), "r3-leather"),
           B("SeatRoll", (2.5, 10.5, 5.75), (13.5, 13, 6.5), "r3-leather", faces=no("south")),
           B("BackFrame", (2, 11, 14.5), (14, 29, 16), wood),
           B("Back", (2.75, 13.5, 13.25), (13.25, 28, 14.5), "r3-leather", faces=no("south")),
           B("BackTop", (2, 29, 13.5), (14, 30, 16), wood)]
    for i, (x, y) in enumerate(((5, 17), (8, 17), (11, 17), (6.5, 22), (9.5, 22))):
        els.append(B(f"Button{i}", (x - 0.25, y - 0.25, 13), (x + 0.25, y + 0.25, 13.25), "r3-black", faces=("north",)))
    for side, x in (("L", 1), ("R", 13)):
        els += [B(f"Arm{side}", (x, 17, 6), (x + 2, 18.5, 15), wood),
                B(f"Cap{side}", (x - 0.1, 17.5, 5.5), (x + 2.1, 18.75, 6.5), "r3-steel"),
                B(f"ArmPost{side}", (x + 0.5, 11, 6.75), (x + 1.5, 17, 7.75), wood, faces=no("up", "down")),
                B(f"ArmSide{side}", (x, 11, 7.75), (x + 2, 17, 14.5), "r3-leather", faces=no("up", "down"))]
    for side, x in (("L", 4.5), ("R", 10)):
        els += [B(f"Post{side}", (x + 0.5, 6, 1.5), (x + 1.25, 9, 2.25), "r3-steel", faces=no("down")),
                B(f"Rest{side}", (x - 0.25, 9, 0), (x + 2, 9.75, 4.5), "r3-steel"),
                B(f"Heel{side}", (x - 0.25, 9.75, 3.25), (x + 2, 11, 4.5), "r3-steel", faces=no("down"))]
    els += [B("Kit", (12.5, 6, 3.25), (15.5, 8.5, 6.25), wood),
            B("KitHandle", (13.75, 8.5, 4.5), (14.25, 10, 5), "r3-steel", faces=no("down")),
            B("Brush", (12.75, 8.5, 3.5), (13.5, 9.25, 6), "r3-black", faces=no("down")),
            B("Tin0", (1.5, 6, 3.75), (3, 6.75, 5.25), "r3-steel", faces=no("down")),
            B("Tin1", (1.75, 6.75, 4), (2.75, 7, 5), "r3-black", faces=("up",))]
    return els


def stall(part):
    # a toilet cubicle, its back to the wall (south): the bowl, partitions left and right, the door ajar at the front
    if part == "upper":
        return [B("PartL", (0, 0, 1), (1, 12, 16), "r3-partition", faces=no("down")),
                B("PartR", (15, 0, 1), (16, 12, 16), "r3-partition", faces=no("down")),
                B("Head", (0, 10, 0), (16, 12, 1), "r3-steel"),
                B("DoorTop", (1, 0, 0.25), (8, 6, 1), "r3-partition", faces=no("down"), rot=(0, -50, 0), origin=(1, 0, 0.6))]
    return [B("PartL", (0, 2, 1), (1, 16, 16), "r3-partition", faces=no("up")),
            B("PartR", (15, 2, 1), (16, 16, 16), "r3-partition", faces=no("up")),
            B("FootL", (0, 0, 2), (1, 2, 3), "r3-steel"),
            B("FootR", (15, 0, 2), (16, 2, 3), "r3-steel"),
            B("Door", (1, 2, 0.25), (8, 16, 1), "r3-partition", faces=no("up"), rot=(0, -50, 0), origin=(1, 0, 0.6)),
            B("Tank", (4.5, 6, 13), (11.5, 13, 16), "r3-porcelain"),
            B("Bowl", (5, 0, 6), (11, 6, 13), "r3-porcelain"),
            B("Seat", (4.5, 6, 5.5), (11.5, 7, 13), "r3-white"),
            B("Roll", (13.5, 7, 9), (15, 9, 11), "r3-white")]


BOTTLES = [(214, 182, 112), (120, 30, 40), (40, 90, 60), (200, 200, 210), (90, 60, 30), (30, 60, 120), (230, 150, 40)]


def gondola():
    """A duty-free gondola: a steel island two shelves high, bottles on both faces (spirits, perfume), a price rail."""
    els = [B("Base", (1, 0, 3), (15, 3, 13), "r3-dark", faces=no("down")),
           B("Spine", (7.5, 3, 3), (8.5, 22, 13), "r3-steel"),
           B("Cap", (1, 22, 3), (15, 23, 13), "r3-dark")]
    rng = random.Random(36)
    for t, y in enumerate((3, 12)):
        els.append(B(f"Shelf{t}", (1, y, 3), (15, y + 0.75, 13), "r3-steel"))
        for side, (z0, z1) in enumerate(((3.5, 7), (9, 12.5))):
            x = 1.6
            k = 0
            while x < 14:
                w = rng.choice((1.6, 2, 2.4))
                h = rng.choice((5, 6, 7))
                col = rng.randrange(len(BOTTLES))
                els.append(B(f"B{t}{side}{k}", (x, y + 0.75, z0), (min(14.6, x + w), y + 0.75 + h, z1), f"r3-bottle{col}", faces=no("down")))
                x += w + 0.4
                k += 1
    return els


def prop_blocks():
    nb = [(0, 0, 0, 1, 1, 1)]
    P.block("l36-meetpost", [("part", ("base", "pole")), ("quad", ("nw", "ne", "sw", "se"))],
            lambda v: meetpost(v["part"], v["quad"]),
            "Level 36: the meeting-point sign's post, a quarter of it in each of four blocks round its middle (quad), the "
            "plinth at the foot (base)",
            boxes=lambda v: [tuple(c / 16 for c in (lambda b: (b[0], 0, b[1], b[2], 16, b[3]))(_corner_box(v["quad"], 4)))], rot="none", material="Metal", sounds=P.METAL,
            data={"attributes": {"l36structure": True}})
    P.block("l36-gondola", [("side", tuple(SIDES))], lambda v: gondola(),
            "Level 36: a duty-free gondola, two steel shelves of bottles on both faces (tinted water: the lore says the "
            "perfumes are worthless)", boxes=[(0.0625, 0, 0.1875, 0.9375, 1.4375, 0.8125)], material="Metal", sounds=P.METAL)
    P.block("l36-charger", [], lambda v: charger(),
            "Level 36: a charging post between the gate seats: sockets and USB ports up a slim white column (the lore's "
            "outlets and USB ports; nothing to charge here)", boxes=[(0.375, 0, 0.375, 0.625, 1.3, 0.625)],
            sel=[(0.3, 0, 0.3, 0.7, 1.3, 0.7)], material="Metal", sounds=P.METAL)
    P.block("l36-payphone", [("side", tuple(SIDES))], lambda v: payphone(),
            "Level 36: a payphone under its stainless hood on a short counter, against the wall behind it; the line is dead",
            boxes=[(0.06, 0, 0.25, 0.94, 1.6, 1)], material="Metal", sounds=P.METAL)
    P.block("l36-atm", [("side", tuple(SIDES))], lambda v: atm(),
            "Level 36: a cash machine in its dark surround; it asks for a card it will never take",
            boxes=[(0, 0, 0.25, 1, 1.85, 1)], material="Metal", sounds=P.METAL)
    P.block("l36-fountain", [("side", tuple(SIDES))], lambda v: fountain(),
            "Level 36: a stainless bi-level drinking fountain against the wall; it runs with Almond Water, as the lore's "
            "fountains do (as Level 4's water coolers)",
            boxes=[(0.06, 0, 0.25, 0.94, 1.125, 1)], material="Metal", sounds=P.METAL,
            data={"class": "BackroomsDispenser", "entityClass": "BackroomsDispenser", "attributes": {"liquidSource": True}})
    P.block("l36-shoeshine", [("side", tuple(SIDES))], lambda v: shoeshine(),
            "Level 36: a shoe-shine chair, red leather, raised on its wooden platform, the foot rests in front",
            boxes=[(0, 0, 0, 1, 0.375, 1), (0.125, 0, 0.375, 0.875, 1, 1)], material="Wood", sounds=P.WOOD)
    P.block("l36-stall", [("part", ("lower", "upper")), ("side", tuple(SIDES))], lambda v: stall(v["part"]),
            "Level 36: a toilet cubicle, its back to the wall: the bowl, laminate partitions either side, the door left ajar "
            "(lower; upper the partitions' tops)",
            boxes=lambda v: [(0, 0, 0.0625, 0.0625, 1, 1), (0.9375, 0, 0.0625, 1, 1, 1)] if v["part"] == "lower" else
            [(0, 0, 0.0625, 0.0625, 0.75, 1), (0.9375, 0, 0.0625, 1, 0.75, 1)],
            sel=lambda v: [(0, 0, 0, 1, 1, 1)] if v["part"] == "lower" else [(0, 0, 0, 1, 0.75, 1)],
            material="Wood", sounds=P.WOOD)


NAMES = {
    "block-l36-art-dep-*": "Departures Board",
    "block-l36-art-arr-*": "Arrivals Board",
    "block-l36-art-welc-*": "Welcome Banner",
    "block-l36-art-m*": "Menu Board",
    "block-l36-art-p0-*": "Travel Agency Poster",
    "block-l36-art-p1-*": "Travel Agency Poster",
    "block-l36-art-p2-*": "Travel Agency Notice",
    "block-l36-art-p6-*": "Unattended Baggage Notice",
    "block-l36-art-p7-*": "Taped-up Warning",
    "block-l36-art-*": "Poster",
    "block-l36-apron-*": "Runway Window",
    "block-l36-colposter-*": "Column Poster",
    "block-l36-meetbox-*": "Meeting Point Sign",
    "block-l36-meetpost-*": "Meeting Point Sign Post",
    "block-l36-finish-coffer": "Coffered Ceiling",
    "block-l36-finish-wood": "Oak Slat Ceiling",
    "block-l36-finish-stone": "Travertine Cladding",
    "block-l36-finish-stonetop": "Travertine Cladding",
    "block-l36-finish-skylight": "Skylight",
    "block-l36-finish-*": "Terminal Finish",
    "block-l36-charger": "Charging Post",
    "block-l36-gondola-*": "Duty-free Gondola",
    "block-l36-payphone-*": "Payphone",
    "block-l36-atm-*": "Cash Machine",
    "block-l36-fountain-*": "Drinking Fountain",
    "block-l36-shoeshine-*": "Shoe-shine Chair",
    "block-l36-stall-*": "Toilet Cubicle",
}


def main():
    P.CODES.clear()
    P.SHAPE_FILES.clear()
    art_pictures()
    apron()
    meetbox()
    finishes()
    surface_blocks()
    _tex_props()
    prop_blocks()
    print(f"gen_36_detail: {len(P.CODES)} prop block types, {len(P.SHAPE_FILES)} shapes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
