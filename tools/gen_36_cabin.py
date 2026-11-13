"""Level 36 "Airport" (experimental): the plane's cabin and the jet bridge's end (cabin pass, 2026-11-13).

The cabin (WorldLayout.Level36.Cabin.cs) is a narrow-body's economy cabin, five wide and three high, seen from the
boarding door (L1, where the jet bridge ends). Every model is drawn facing north (its front toward -z) and turned by its
`side`; the cabin's walls face into the cabin, the overheads face the aisle, the seats face the nose. Every plane has the
same hand (it boards on its left), so a wall model on the boarding side has the nose toward -x, one on the far side
toward +x.

Contract blocks (the flight's logic, on its own branch, swaps them by name):
    l36-cabinwindow-{apron,roll,climb,cruise,descent,ground}-{side}   the sidewall with its porthole (reveal, frame, blind
                                    up), the pane's picture by the flight's phase, glowing
    l36-psu-{off,on}-{side}         the passenger service unit under the outer bin (reading lights, air nozzles, the
                                    FASTEN SEAT BELT / NO SMOKING sign dark or lit)
    l36-ceiling-cabin / l36-ceiling-cabin-dim   the aisle's lit ceiling, and the same with the lights down
    l36-planedoor-{open,closed}-{lower,upper}-{side}   the boarding door at the bridge's end, two blocks high
Others:
    l36-cabinblind-{side}           a window with its blind down (never swapped)
    l36-cabinside-{lower,plain,upper}-{side}   the sidewall below the windows, between them, curving in above
    l36-cabinbin-{r10..r18,openbag,opencoat}-{side}   an overhead bin (its row number on the lip; open with a bag, a coat)
    l36-cabinfloor-{track,aisle}-{ns,we}, l36-cabinfloor-vinyl   seat-track carpet, the aisle with its path lights, galley
    l36-cabinseat-{side} (rebuilt), l36-cabinseat2-{blanket,pillow,bag,magazine,exitrow}-{side}
    l36-cabinsign-{side}            an EXIT sign hung over the aisle
    l36-doorhead-{side}             over a door: the lit EXIT sign inside, the skin and the bridge's canopy outside
    l36-doorside-{fwd,aft}{low,mid,top}-{side}   the fuselage either side of the boarding door: sidewall inside, the white
                                    skin with the cheatline and the canopy's bellows toward the bridge
    l36-cabindoor-{port,stbd}-{lower,upper}-{side}   a closed door (R1, L2, R2) seen from inside
    l36-cabinexit-{lower,upper}-{side}   an overwing exit hatch
    l36-bulkhead-{low,mid,midext,top}-{side}, l36-fddoor-{lower,upper}-{side}   the forward bulkhead and the flight deck's door
    l36-galley-{carts,cartswaste,oven,coffee,counter,stow}-{side}, l36-lav-{doorlow,doorocc,doorvac,top,body}-{side},
    l36-jumpseat-{side}, l36-curtain-{lower,mid,top}-{side}

Run from the worktree root, under the asset lock:  bash tools/locked.sh run python tools/gen_36_cabin.py  (gen_36.py runs it)
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matlib as M  # noqa: E402
import gen_36_props as P  # noqa: E402
import gen_36_cabin_tex as CT  # noqa: E402
import modelkit as MK  # noqa: E402
from gen_textures import check_atlas_grid  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
CABTEX = os.path.join(ASSETS, "textures", "block", "36", "cabin")
PROPTEX = os.path.join(ASSETS, "textures", "block", "36", "props")
SHAPES = os.path.join(ASSETS, "shapes", "block", "36", "cabin")
S = 32
SIDES = P.SIDES
DIRS = MK.DIRS
no = P.no
PHASES = ("apron", "roll", "climb", "cruise", "descent", "ground")
PHASE_LIGHT = {"apron": 6, "roll": 6, "climb": 8, "cruise": 10, "descent": 4, "ground": 0}
PHASE_GLOW = {"apron": 90, "roll": 100, "climb": 140, "cruise": 180, "descent": 70, "ground": 40}
ROWS = (10, 11, 12, 14, 15, 16, 17, 18)


def B(name, frm, to, tex, faces=None, glow=0, rot=None, origin=None, uv=None):
    return MK.box(name, frm, to, tex, faces=DIRS if faces is None else faces, glow=glow, rot=rot, origin=origin, uv=uv)


def pic(el, face, key, uv=(0, 0, 16, 16), glow=0):
    el["faces"][face] = {"texture": "#" + key, "uv": list(uv)}
    if glow:
        el["faces"][face]["glow"] = glow
    return el


def shift(els, dx=0, dy=0, dz=0):
    out = json.loads(json.dumps(els))
    for e in out:
        e["from"] = [round(e["from"][0] + dx, 4), round(e["from"][1] + dy, 4), round(e["from"][2] + dz, 4)]
        e["to"] = [round(e["to"][0] + dx, 4), round(e["to"][1] + dy, 4), round(e["to"][2] + dz, 4)]
        if "rotationOrigin" in e:
            o = e["rotationOrigin"]
            e["rotationOrigin"] = [round(o[0] + dx, 4), round(o[1] + dy, 4), round(o[2] + dz, 4)]
    return out


def renamed(els, prefix):
    out = json.loads(json.dumps(els))
    for e in out:
        e["name"] = prefix + e["name"]
    return out


# ======================================================================== Materials

def _save(img, name):
    img = img.convert("RGBA")
    a = np.asarray(img).copy()
    a[..., 3] = 255
    img = Image.fromarray(a, "RGBA")
    check_atlas_grid(img, f"block/36/cabin/{name}.png")
    os.makedirs(CABTEX, exist_ok=True)
    img.save(os.path.join(CABTEX, name + ".png"))


def _arr(img):
    return np.asarray(img.convert("RGBA")).astype(np.float64)


def _img(a):
    a = np.clip(np.rint(a), 0, 255).astype(np.uint8)
    a[..., 3] = 255
    return Image.fromarray(a, "RGBA")


PLASTIC = (230, 228, 220)


def materials():
    sd = 3600
    # cabin plastic: the moulded panels, a soft sheen down the panel, never flat
    pl = M.plaster(sd, base=PLASTIC, grain=2, mottle=3, roller=0.1, bumps=0)
    a = _arr(pl)
    a[..., :3] += (5 - 10 * (np.arange(S) / S))[:, None, None]
    _save(_img(a), "c-panel")
    a = _arr(M.plaster(sd + 1, base=(212, 210, 204), grain=2, mottle=3, roller=0.1, bumps=0))
    _save(_img(a), "c-trim")
    _save(M.noise_hv((132, 134, 140), 2, sd + 2, S, 3), "c-grey")
    _save(M.noise_hv((84, 86, 92), 2, sd + 3, S, 2), "c-dark")
    # the PSU's panel: light grey, a fine perforated grille band (the speaker), a seam
    a = _arr(M.noise_hv((214, 214, 210), 1.5, sd + 4, S, 2))
    for y in range(22, 27, 2):
        for x in range(20, 29, 2):
            a[y, x, :3] -= 30
    a[0, :, :3] -= 30
    a[31, :, :3] -= 30
    _save(_img(a), "c-psu")
    lens = Image.new("RGBA", (S, S), (255, 250, 232, 255))
    d = ImageDraw.Draw(lens)
    d.ellipse((4, 4, 27, 27), fill=(255, 255, 248, 255))
    d.ellipse((10, 10, 21, 21), fill=(255, 255, 255, 255))
    _save(lens, "c-lens")
    _save(Image.new("RGBA", (S, S), (255, 244, 214, 255)), "c-led")
    _save(Image.new("RGBA", (S, S), (255, 176, 60, 255)), "c-strip")
    _save(M.painted_metal(sd + 20, base=(196, 30, 32), grain=2, mottle=3, panel=False, chips=0), "c-red")
    _save(M.noise_hv((200, 214, 218), 2, sd + 21, S, 2), "c-glass")
    _save(M.noise_hv((74, 44, 26), 3, sd + 22, S, 3), "c-coffee")
    _save(M.fabric(seed=sd + 5, base=(62, 64, 70), weave="plain", contrast=5, grain=2, mottle=3), "c-binin")
    # the ceiling: white with a faint lengthwise seam
    a = _arr(M.plaster(sd + 6, base=(238, 238, 234), grain=1.5, mottle=2, roller=0.1, bumps=0))
    _save(_img(a), "c-ceil")
    # the blind: light grey plastic with fine ribs
    a = _arr(M.noise_hv((206, 206, 200), 1.5, sd + 7, S, 2))
    for y in range(0, S, 4):
        a[y, :, :3] -= 18
        a[y + 1, :, :3] += 6
    _save(_img(a), "c-blind")
    # the air-return grille in the dado: dark slots
    a = _arr(M.noise_hv((176, 176, 172), 1.5, sd + 8, S, 2))
    for y in range(4, 28, 4):
        a[y:y + 2, 2:30, :3] = (44, 46, 50)
    _save(_img(a), "c-grille")
    # the lavatory door's louvre and the flight deck's door: painted grey
    a = _arr(M.painted_metal(sd + 9, base=(196, 198, 200), grain=2, mottle=3, panel=False, chips=0))
    _save(_img(a), "c-fddoor")
    a = _arr(M.noise_hv((200, 198, 192), 1.5, sd + 10, S, 2))
    for y in range(2, 30, 3):
        a[y, 2:30, :3] -= 46
        a[y + 1, 2:30, :3] += 10
    _save(_img(a), "c-louvre")
    # carpets: the cabin's navy-grey with a fleck; the seats' aluminium tracks run along it (ns: along v)
    base = M.carpet(seed=sd + 11, base=(58, 66, 98), tone2=(46, 52, 80), mix2=0.3, pile=6, grain=3, mottle=4)
    _save(base, "c-carpet")
    for axis in ("ns", "we"):
        a = _arr(base)
        for t in (5, 26):
            if axis == "ns":
                a[:, t:t + 2, :3] = (170, 174, 180)
                a[:, t + 2, :3] = (60, 62, 68)
                a[::4, t:t + 2, :3] = (90, 92, 98)
            else:
                a[t:t + 2, :, :3] = (170, 174, 180)
                a[t + 2, :, :3] = (60, 62, 68)
                a[t:t + 2, ::4, :3] = (90, 92, 98)
        _save(_img(a), f"c-track-{axis}")
    aisle = M.carpet(seed=sd + 12, base=(86, 92, 130), tone2=(66, 72, 106), mix2=0.35, pile=6, grain=3, mottle=4)
    _save(aisle, "c-aisle")
    a = _arr(M.noise_hv((150, 152, 150), 3, sd + 13, S, 4))
    rng = np.random.default_rng(sd)
    for _ in range(70):
        x, y = rng.integers(0, S, 2)
        a[y, x, :3] += rng.choice((-30, 26))
    _save(_img(a), "c-vinyl")
    # the overhead bin's door: a moulded panel, a sheen toward its top
    a = _arr(M.plaster(sd + 14, base=(234, 232, 226), grain=1.5, mottle=2, roller=0.1, bumps=0))
    a[..., :3] += (8 - 14 * (np.arange(S) / S))[:, None, None]
    a[0:2, :, :3] -= 20
    _save(_img(a), "c-bindoor")
    # the fuselage's skin beside the door, the cheatline at the door's own height (its teal at the foot of the window block,
    # the amber pinstripe at the top of the block under it)
    sk = _arr(Image.open(os.path.join(CABTEX, "skin.png")))
    a = sk.copy()
    a[27:31, :, :3] = (18, 92, 120)
    a[26, :, :3] = (40, 112, 138)
    _save(_img(a), "c-skinband")
    a = sk.copy()
    a[2:4, :, :3] = (255, 200, 80)
    _save(_img(a), "c-skinpin")
    # the lit ceiling (l36-ceiling-cabin) and its dimmed state: a diffuser over the aisle
    for name, col, edge in (("l36-ceiling-cabin", (252, 250, 240), (226, 226, 220)), ("l36-ceiling-cabin-dim", (118, 132, 168), (92, 98, 116))):
        img = Image.new("RGBA", (S, S), col + (255,))
        a = _arr(img)
        a[..., :3] += np.random.default_rng(sd + 15).normal(0, 1.2, (S, S, 1))
        a[0, :, :3] = a[0, :, :3] * 0.6 + np.array(edge) * 0.4
        a[:, 0, :3] = a[:, 0, :3] * 0.6 + np.array(edge) * 0.4
        im = _img(a)
        check_atlas_grid(im, f"block/36/{name}.png")
        im.save(os.path.join(ASSETS, "textures", "block", "36", name + ".png"))


def tex_path(key):
    if os.path.exists(os.path.join(CABTEX, key + ".png")):
        return "backrooms:block/36/cabin/" + key
    if os.path.exists(os.path.join(PROPTEX, key + ".png")):
        return "backrooms:block/36/props/" + key
    raise KeyError(key)


SHAPE_FILES = []


def shape(name, els):
    keys = sorted({f["texture"][1:] for e in els for f in e["faces"].values()})
    names = [e["name"] for e in els]
    assert len(names) == len(set(names)), (name, [n for n in names if names.count(n) > 1])
    P.write_json(os.path.join(SHAPES, name + ".json"),
                 {"textureWidth": 16, "textureHeight": 16, "textures": {k: tex_path(k) for k in keys}, "elements": els})
    SHAPE_FILES.append(name)
    return "backrooms:block/36/cabin/" + name


# ======================================================================== The sidewall

PANEL = {"all": "c-panel"}


def side_lower():
    """The sidewall under the windows: the dado panel, the air-return grille, a dark kick strip on the carpet."""
    return [B("Panel", (0, 1.5, 1.5), (16, 16, 16), "c-panel", faces=("north",)),
            B("Kick", (0, 0, 0.75), (16, 1.5, 16), "c-grey", faces=("north", "up")),
            B("Grille", (1.5, 2.5, 1.2), (14.5, 4.5, 1.5), "c-grille", faces=("north", "up", "down", "east", "west"), uv=(0, 0, 16, 16)),
            B("Seam", (0, 15.5, 1.25), (16, 16, 1.5), "c-trim", faces=("north", "down"))]


def side_upper():
    """Over the windows: the sidewall curving in toward the bins and the ceiling (a plate leaning into the cabin)."""
    return [B("Curve", (0, 0, 1.5), (16, 16.6, 3), "c-panel", faces=("north",), rot=(22.5, 0, 0), origin=(8, 0, 1.5)),
            B("Top", (0, 15.2, -4.9), (16, 16, 1.5), "c-ceil", faces=("down",))]


def side_plain():
    return [B("Panel", (0, 0, 1.5), (16, 16, 16), "c-panel", faces=("north",)),
            B("Seam", (0, 0, 1.25), (0.4, 16, 1.5), "c-trim", faces=("north", "east"))]


def porthole(shut=False, view=None, glow=0):
    """The window panel: a plate round a rounded porthole (6.5 x 9), its reveal going back to the pane, a raised bezel, the
    blind stowed at the top (or drawn down)."""
    x0, x1, y0, y1 = 4.75, 11.25, 4, 13
    zp = 1.5
    els = [B("PlL", (0, 0, zp), (x0, 16, 16), "c-panel", faces=("north", "east")),
           B("PlR", (x1, 0, zp), (16, 16, 16), "c-panel", faces=("north", "west")),
           B("PlT", (x0, y1, zp), (x1, 16, 16), "c-panel", faces=("north", "down")),
           B("PlB", (x0, 0, zp), (x1, y0, 16), "c-panel", faces=("north", "up"))]
    # rounded corners: small plates turned 45 degrees across each corner of the opening
    for i, (cx, cy) in enumerate(((x0, y0), (x1, y0), (x0, y1), (x1, y1))):
        els.append(B(f"Corner{i}", (cx - 1.3, cy - 1.3, zp + 0.05), (cx + 1.3, cy + 1.3, zp + 3.4), "c-trim", faces=("north", "up", "down", "east", "west"),
                     rot=(0, 0, 45), origin=(cx, cy, zp)))
    # the bezel standing proud of the panel, and the reveal back to the pane
    w = 0.6
    els += [B("BzT", (x0 - w, y1, zp - 0.5), (x1 + w, y1 + w, zp), "c-trim", faces=("north", "up", "down", "east", "west")),
            B("BzB", (x0 - w, y0 - w, zp - 0.5), (x1 + w, y0, zp), "c-trim", faces=("north", "up", "down", "east", "west")),
            B("BzL", (x0 - w, y0, zp - 0.5), (x0, y1, zp), "c-trim", faces=("north", "east", "west")),
            B("BzR", (x1, y0, zp - 0.5), (x1 + w, y1, zp), "c-trim", faces=("north", "east", "west")),
            B("RvT", (x0, y1 - 0.5, zp), (x1, y1, 5), "c-trim", faces=("down",)),
            B("RvB", (x0, y0, zp), (x1, y0 + 0.5, 5), "c-trim", faces=("up",)),
            B("RvL", (x0, y0, zp), (x0 + 0.5, y1, 5), "c-trim", faces=("east",)),
            B("RvR", (x1 - 0.5, y0, zp), (x1, y1, 5), "c-trim", faces=("west",))]
    if shut:
        els += [B("Blind", (x0 + 0.5, y0 + 0.5, 3), (x1 - 0.5, y1 - 0.5, 3.3), "c-blind", faces=("north",), uv=(0, 0, 16, 16)),
                B("Tab", (7.25, y0 + 0.4, 2.6), (8.75, y0 + 1.3, 3), "c-grey", faces=("north", "up", "down", "east", "west"))]
    else:
        els += [pic(B("Pane", (x0 + 0.5, y0 + 0.5, 5), (x1 - 0.5, y1 - 0.5, 5.4), "c-grey", faces=("north",)), "north", view, glow=glow),
                B("Blind", (x0 + 0.5, y1 - 1.6, 3), (x1 - 0.5, y1 - 0.5, 3.3), "c-blind", faces=("north", "down"), uv=(0, 0, 16, 4)),
                B("Tab", (7.25, y1 - 2.2, 2.6), (8.75, y1 - 1.5, 3), "c-grey", faces=("north", "up", "down", "east", "west"))]
    return els


# ======================================================================== Overheads

def psu(lit):
    """The passenger service unit under the outer bin (over the window seat), facing the aisle: its panel, two reading
    lights, two air nozzles, the call button, the sign; the bin's body over it; a fairing down to the sidewall."""
    els = [B("Body", (0, 2, 0), (16, 16, 16), "c-panel", faces=("east", "west")),
           B("Panel", (0, 0.4, 0), (16, 2, 17.5), "c-psu", faces=("down", "east", "west"), uv=(0, 0, 16, 16))]
    for i, x in enumerate((3, 10.5)):
        els += [B(f"Light{i}", (x, 0.3, 6), (x + 2, 0.4, 8), "c-lens", faces=("down",), glow=120),
                B(f"Gasper{i}", (x + 0.5, 0.0, 2.8), (x + 1.5, 0.4, 3.8), "chrome", faces=("down", "north", "south", "east", "west"))]
    els += [B("Call", (6.5, 0.3, 7), (7.3, 0.4, 7.8), "c-grey", faces=("down",)),
            pic(B("Sign", (5.75, 0.15, 10), (10.25, 0.4, 12.25), "c-dark", faces=("north", "south", "east", "west")), "down",
                "sign-psu-on" if lit else "sign-psu-off", glow=255 if lit else 0),
            B("Mask", (1.5, 0.3, 13), (14.5, 0.4, 14.6), "c-trim", faces=("down",))]
    return els


def bin_block(state):
    """An overhead bin over the aisle seat, its door toward the aisle (north): the door with its latch, the lip with the
    row's number, the PSU's strip under it (the aisle seat's light and nozzle), the ceiling's cove rising from its top
    into the aisle, an LED strip lighting the cove; open, the door swung up and a bag or a coat in it."""
    open_ = state in ("openbag", "opencoat")
    els = [B("Under", (0, 0.4, 0), (16, 1.6, 16), "c-psu", faces=("down", "east", "west"), uv=(0, 0, 16, 16)),
           B("Lip", (0, 0.6, -0.5), (16, 2.2, 0.5), "c-trim", faces=("north", "down", "up", "east", "west")),
           B("Light", (3, 0.3, 9), (5, 0.4, 11), "c-lens", faces=("down",), glow=120),
           B("Gasper", (7, 0.0, 9.5), (8, 0.4, 10.5), "chrome", faces=("down", "north", "south", "east", "west")),
           # the cove: the ceiling's curve from the bin's top into the aisle, in two plates, and the light along its foot
           B("Cove1", (0, 11.4, -3.6), (16, 12, 0.6), "c-ceil", faces=("down", "east", "west"), rot=(-38, 0, 0), origin=(8, 11.4, 0.6)),
           B("Cove2", (0, 14.2, -6.6), (16, 14.8, -2.2), "c-ceil", faces=("down", "east", "west"), rot=(-18, 0, 0), origin=(8, 14.2, -2.2)),
           B("Led", (0, 11, -0.4), (16, 11.5, 0.6), "c-led", faces=("north", "up"), glow=200)]
    if not open_:
        n = ROWS.index(int(state[1:]))
        u, v = (n % 4) * 4, (n // 4) * 4
        els += [B("Body", (0, 2, 1), (16, 11.4, 16), "c-panel", faces=("east", "west", "up")),
                B("Door", (0.2, 2.2, 0), (15.8, 11, 1.2), {"north": "c-bindoor", "all": "c-trim"}, faces=("north", "east", "west", "up"),
                  uv=None),
                B("Latch", (7.1, 2.6, -0.2), (8.9, 3.1, 0), "c-grey", faces=("north", "up", "down", "east", "west")),
                pic(B("Num", (13, 0.8, -0.6), (15.4, 2.0, -0.5), "c-trim", faces=()), "north", "rownums", uv=(u, v + 1, u + 4, v + 3))]
        els[-3]["faces"]["north"]["uv"] = [0, 0, 16, 16]
        return els
    els += [B("Floor", (0.3, 1.6, 1), (15.7, 2.2, 15.5), "c-binin", faces=("up",)),
            B("BackW", (0.3, 2.2, 15), (15.7, 11, 15.5), "c-binin", faces=("north",)),
            B("Roof", (0.3, 10.5, 1), (15.7, 11, 15.5), "c-binin", faces=("down",)),
            B("SideW", (0, 2.2, 1), (0.3, 11, 15.5), "c-panel", faces=("east", "west")),
            B("SideE", (15.7, 2.2, 1), (16, 11, 15.5), "c-panel", faces=("east", "west")),
            # the door swung up on its hinge at the top, its inside showing
            B("Door", (0.2, 11, -8.8), (15.8, 12.2, 0), {"down": "c-trim", "all": "c-bindoor"}, faces=("down", "up", "north", "east", "west"),
              rot=(-28, 0, 0), origin=(8, 11.6, 0))]
    if state == "openbag":
        els += [B("Bag", (2, 2.2, 3), (10.5, 9.4, 14.5), "pack-dark", faces=no("south")),
                B("BagPanel", (2.6, 2.8, 2.7), (9.9, 8.8, 3), "pack", faces=("north",)),
                B("Handle", (5, 9.4, 3.2), (7.5, 10.2, 4), "black", faces=no("down")),
                B("Bag2", (11, 2.2, 6), (15.4, 6.5, 14.5), "duffel", faces=no("south"))]
    else:
        els += [B("Coat", (1.5, 2.2, 2), (13, 6, 14.5), "jacket", faces=no("south")),
                B("Sleeve", (7, -7, -0.6), (10, 2.6, 1.6), "jacket", faces=no("up"), rot=(0, 0, 8), origin=(8.5, 2.6, 0.5)),
                B("Cuff", (7.1, -7.8, -0.5), (9.9, -7, 1.5), "jacket-dark", faces=no("up"), rot=(0, 0, 8), origin=(8.5, 2.6, 0.5)),
                B("Lining", (2, 2.4, 1.5), (12.5, 2.8, 2.1), "jacket-dark", faces=("north",))]
    return els


def exit_sign():
    """An EXIT sign hung over the aisle, lettered on both faces."""
    return [pic(pic(B("Box", (3, 9.5, 6.75), (13, 13.5, 9.25), "c-dark", faces=("east", "west", "down", "up")), "north", "sign-exit", glow=255),
                "south", "sign-exit", glow=255),
            B("Stem", (7.5, 13.5, 7.5), (8.5, 16, 8.5), "chrome", faces=("north", "south", "east", "west")),
            B("Plate", (6, 15.6, 6.5), (10, 16, 9.5), "c-trim", faces=("down", "north", "south", "east", "west"))]


# ======================================================================== Seats

CAB = {"top": "cabin", "front": "cabin", "side": "cabin-side", "back": "cabin-side", "bottom": "cabin-side"}


def seat(kind="plain"):
    """An economy seat facing north: legs on the floor's tracks, the pan and cushion, the back leaning, the headrest cover,
    armrests at both edges (two seats side by side share one), the tray and its latch, the seat pocket with the safety
    card and the magazine, the life-vest pouch, the belt buckled across the seat."""
    els = []
    for i, x in enumerate((2.6, 12.6)):
        els += [B(f"LegF{i}", (x, 0.3, 3), (x + 0.9, 5.5, 3.9), "steelv", faces=no("up", "down"), rot=(-12, 0, 0), origin=(x, 0.3, 3.4)),
                B(f"LegB{i}", (x, 0.3, 10.8), (x + 0.9, 5.5, 11.7), "steelv", faces=no("up", "down")),
                B(f"Rail{i}", (x - 0.2, 0, 2.4), (x + 1.1, 0.5, 12.4), "darksteel", faces=no("down"))]
    els += [B("Beam", (1.75, 4.6, 4), (14.25, 5.4, 4.8), "steel", faces=("north", "south", "down")),
            B("BeamB", (1.75, 4.6, 10.7), (14.25, 5.4, 11.5), "steel", faces=("north", "south", "down")),
            B("Pan", (1.5, 5.4, 2.2), (14.5, 6.2, 12.6), "darkplastic", faces=no("up")),
            B("Cushion", (1.5, 6.2, 1.9), (14.5, 8.6, 12.4), CAB, faces=no("down")),
            B("Roll", (1.5, 5.9, 1.4), (14.5, 8.3, 1.9), CAB, faces=no("south", "down")),
            B("Seam", (1.6, 8.6, 6.8), (14.4, 8.7, 7.2), "cabin-side", faces=("up",)),
            pic(B("Vest", (5, 4.4, 2.3), (11, 5.4, 3.8), "darkplastic", faces=("east", "west", "down")), "north", "placard-lifevest", uv=(0, 0, 16, 16))]
    back = [B("Shell", (1.5, 7.5, 13), (14.5, 24, 14.3), "darkplastic", faces=no("north")),
            B("Back", (1.5, 8.5, 11.4), (14.5, 23, 13), CAB, faces=no("south", "down")),
            B("Bolster", (1.5, 10, 11.0), (2.8, 22, 11.4), "cabin-side", faces=("north", "west")),
            B("BolsterE", (13.2, 10, 11.0), (14.5, 22, 11.4), "cabin-side", faces=("north", "east")),
            B("Cover", (3.5, 20.2, 11.1), (12.5, 23.3, 11.4), "headcover", faces=no("south")),
            B("CoverTop", (3.5, 23.3, 11.1), (12.5, 24.5, 14.6), "headcover", faces=no("down")),
            B("CoverBack", (3.5, 21.6, 14.3), (12.5, 23.3, 14.6), "headcover", faces=("south", "east", "west", "down")),
            B("Tray", (2.8, 13.4, 14.3), (13.2, 19.8, 14.8), "lightplastic", faces=no("north")),
            B("TrayLip", (2.8, 13.2, 14.3), (13.2, 13.6, 15), "darkplastic", faces=("south", "down", "east", "west")),
            B("Latch", (7.1, 19.8, 14.3), (8.9, 20.6, 15), "darkplastic", faces=no("north")),
            B("Pocket", (2.8, 8.6, 14.3), (13.2, 12.4, 15.1), "cabin-side", faces=no("north")),
            pic(B("Card", (3.6, 11.2, 14.5), (6.6, 13.6, 14.7), "c-trim", faces=("east", "west", "up")), "south", "safetycard", uv=(0, 0, 16, 10)),
            pic(B("Mag", (7, 10.8, 14.4), (11.6, 13.4, 14.6), "c-trim", faces=("east", "west", "up")), "south", "magazine", uv=(0, 0, 16, 10))]
    if kind == "exitrow":
        back.append(pic(B("ExitPlacard", (4.5, 20.8, 14.6), (11.5, 22.6, 14.7), "c-trim", faces=()), "south", "placard-exitrow"))
    els += P.turned(back, rx=-10, origin=(8, 8, 12.5))
    for s, x in (("W", 0), ("E", 14.9)):
        els += [B(f"ArmPost{s}", (x + 0.15, 5, 9.4), (x + 0.95, 11.5, 10.6), "darkplastic", faces=no("up", "down")),
                B(f"Arm{s}", (x, 11.5, 3.4), (x + 1.1, 12.7, 12.8), "darkplastic", faces=no("down") if s == "W" else no("down")),
                B(f"ArmCap{s}", (x + 0.05, 12.7, 3.8), (x + 1.05, 13, 12.4), "rubber", faces=("up", "north", "east", "west")),
                B(f"ArmEnd{s}", (x, 10.6, 3.0), (x + 1.1, 12.7, 3.4), "darkplastic", faces=("north", "east", "west", "down"))]
    els += [B("Recline", (14.9, 12.75, 4.4), (15.6, 13.0, 5.2), "chrome", faces=("up", "north", "east", "west")),
            B("BeltW", (1.5, 8.6, 6.1), (7.2, 8.85, 7.6), "webgrey", faces=no("down")),
            B("BeltE", (8.8, 8.6, 6.1), (14.5, 8.85, 7.6), "webgrey", faces=no("down")),
            B("Buckle", (6.9, 8.6, 5.9), (9.1, 9.1, 7.8), "chrome", faces=no("down")),
            B("BeltDropW", (1.35, 6.3, 6.1), (1.5, 8.7, 7.6), "webgrey", faces=("west",)),
            B("BeltDropE", (14.5, 6.3, 6.1), (14.65, 8.7, 7.6), "webgrey", faces=("east",))]
    if kind == "blanket":
        els += [B("Blanket", (2.5, 8.6, 2.4), (13.5, 10.4, 9.5), "blanket", faces=no("down")),
                B("BlanketFold", (2.5, 10.4, 3.2), (13.5, 11.0, 8.7), "blanket", faces=no("down"))]
    elif kind == "pillow":
        els += P.turned([B("Pillow", (3.5, 8.8, 9), (12.5, 15.8, 11.2), "pillow", faces=no("south"))], rx=-14, origin=(8, 8.8, 11))
    elif kind == "bag":
        els += [B("Bag", (3.5, 0, -2.5), (12.5, 5.2, 3.5), "pack", faces=no("down")),
                B("BagPocket", (5, 0.6, -2.9), (11, 3.6, -2.5), "pack-dark", faces=no("down", "south")),
                B("BagHandle", (6.5, 5.2, -0.5), (9.5, 5.8, 1), "strap", faces=no("down"))]
    elif kind == "magazine":
        els += [pic(B("Dropped", (4, 0, -5.5), (9, 0.25, -0.5), "c-trim", faces=("north", "south", "east", "west")), "up", "magazine", uv=(0, 0, 16, 16),),
                B("Mag", (7, 10.8, 14.4), (11.6, 13.4, 14.6), "c-trim", faces=())]
        els = [e for e in els if e["name"] != "Mag" or e["faces"]]
        # (the pocket's own magazine is the one on the floor)
        els = [e for e in els if e["name"] != "Mag"]
    return els


# ======================================================================== Doors

def door_leaf_inner(x0, x1, y0, y1, z, face, slab="c-panel", half=None):
    """The door's inner lining (door-lining) over [x0..x1, y0..y1] at depth z, facing `face` (north or south), cut to
    `half` (lower: the texture's lower half, upper: its upper half)."""
    uv = (0, 8, 16, 16) if half == "lower" else (0, 0, 16, 8) if half == "upper" else (0, 0, 16, 16)
    if face == "north":
        el = B("Lining", (x0, y0, z), (x1, y1, z + 1.2), slab, faces=("east", "west", "up", "down"))
        return pic(el, "north", "door-lining", uv)
    el = B("Lining", (x0, y0, z - 1.2), (x1, y1, z), slab, faces=("east", "west", "up", "down"))
    # (seen from +z the texture's left is -x: turn it round so the leaf reads as the same door)
    return pic(el, "south", "door-lining", uv)


def planedoor(state, part):
    """The boarding door in the fuselage, facing the cabin (north); the bridge is to the south. Its frame (jambs, sill, a
    header with rounded corners, a seal toward the skin), an assist handle on the aft jamb (+x). Closed: the leaf in the
    opening (lining, handle, viewport, slide bustle inside; the skin outside). Open: the leaf swung forward against the
    skin outside (x -14..-1, toward the bridge), its inner face with the slide bustle showing."""
    lower = part == "lower"
    els = [B("JambF", (0, 0, 1.5), (1.5, 16, 16), {"all": "c-trim", "south": "skin"}, faces=("north", "east", "south")),
           B("JambA", (14.5, 0, 1.5), (16, 16, 16), {"all": "c-trim", "south": "skin"}, faces=("north", "west", "south")),
           B("SealF", (1.2, 0, 15.8), (1.6, 16, 16.3), "rubber", faces=("south", "east")),
           B("SealA", (14.4, 0, 15.8), (14.8, 16, 16.3), "rubber", faces=("south", "west"))]
    if lower:
        els += [B("Sill", (0, 0, 1.5), (16, 1, 16), {"all": "c-trim", "up": "tread"}, faces=("up", "north", "south")),
                B("SillCap", (1.5, 1, 4), (14.5, 1.15, 14), "chrome", faces=("up",))]
    else:
        els += [B("Head", (0, 14, 1.5), (16, 16, 16), {"all": "c-trim", "south": "skin"}, faces=("down", "north", "south")),
                B("CornF", (0.6, 12.6, 1.5), (3.4, 15.4, 16), "c-trim", faces=("down", "north", "east", "south"), rot=(0, 0, 45), origin=(2, 14, 8)),
                B("CornA", (12.6, 12.6, 1.5), (15.4, 15.4, 16), "c-trim", faces=("down", "north", "west", "south"), rot=(0, 0, 45), origin=(14, 14, 8)),
                B("Assist", (14.8, 1, 0.6), (15.4, 9, 1.2), "chrome", faces=("north", "east", "west", "up", "down")),
                B("AssistM1", (14.8, 1, 1.2), (15.4, 1.6, 1.5), "chrome", faces=("east", "west", "up")),
                B("AssistM2", (14.8, 8.4, 1.2), (15.4, 9, 1.5), "chrome", faces=("east", "west", "down"))]
    if state == "closed":
        y0, y1 = (1, 16) if lower else (0, 14)
        leaf = [door_leaf_inner(1.5, 14.5, y0, y1, 3, "north", half=part),
                pic(B("Skin", (1.5, y0, 4.2), (14.5, y1, 16), "c-trim", faces=()), "south", "door-skin", (0, 8, 16, 16) if lower else (0, 0, 16, 8))]
        if lower:
            leaf += [B("Bustle", (1.9, 1, 1.4), (14.1, 7.6, 3), {"all": "c-grey", "north": "c-grey"}, faces=("north", "up", "east", "west")),
                     pic(B("Girt", (1.9, 6.2, 1.3), (14.1, 6.9, 1.4), "c-grey", faces=()), "north", "door-lining", (0, 15, 16, 15.5)),
                     B("Handle", (4.5, 13.2, 1.8), (11.5, 14.2, 3), "chrome", faces=no("south"))]
            leaf = [e for e in leaf if e["faces"]]
        else:
            leaf += [B("Vp0", (6, 4.6, 2.4), (10, 5.2, 3), "c-grey", faces=("north", "up")),
                     B("Vp1", (6, 9.4, 2.4), (10, 10, 3), "c-grey", faces=("north", "down")),
                     B("Vp2", (5.4, 5.2, 2.4), (6, 9.4, 3), "c-grey", faces=("north", "east")),
                     B("Vp3", (10, 5.2, 2.4), (10.6, 9.4, 3), "c-grey", faces=("north", "west"))]
        els += leaf
    else:
        # the leaf against the skin forward of the door, its lining toward the bridge
        y0, y1 = (0.5, 16) if lower else (0, 14.5)
        lin = door_leaf_inner(-14, -1, y0, y1, 17.8, "south", half=part)
        lin["name"] = "Leaf"
        els += [lin, B("LeafBack", (-14, y0, 16.1), (-1, y1, 16.6), "skin", faces=("east", "west", "up", "down"))]
        if lower:
            els += [B("Bustle", (-13.6, 0.5, 17.8), (-1.4, 7.6, 19.3), {"all": "c-grey"}, faces=("south", "up", "east", "west")),
                    B("Girt", (-13.6, 6.0, 19.3), (-1.4, 6.6, 19.45), "c-trim", faces=("south",)),
                    B("Handle", (-11, 13.2, 17.8), (-4, 14.2, 19), "chrome", faces=no("north")),
                    B("Arm", (-1.5, 12.5, 16), (1.5, 14, 17.6), "darksteel", faces=no("north"))]
            els[-3]["faces"]["south"] = {"texture": "#door-lining", "uv": [0, 12.5, 16, 15]}
        else:
            els += [B("Vp0", (-9.4, 4.6, 17.8), (-5.6, 5.2, 18.4), "c-grey", faces=("south", "up")),
                    B("Vp1", (-9.4, 9.4, 17.8), (-5.6, 10, 18.4), "c-grey", faces=("south", "down")),
                    B("Vp2", (-10, 5.2, 17.8), (-9.4, 9.4, 18.4), "c-grey", faces=("south", "west")),
                    B("Vp3", (-5.6, 5.2, 17.8), (-5, 9.4, 18.4), "c-grey", faces=("south", "east")),
                    B("LeafAssist", (-13.2, 2, 17.8), (-12.6, 10, 18.6), "chrome", faces=("south", "east", "west", "up", "down"))]
    return els


def cabindoor(hand, part):
    """A closed door (R1, L2, R2) from inside: the planedoor's frame and leaf; on the starboard side mirrored."""
    els = [e for e in planedoor("closed", part) if e["name"] not in ("SealF", "SealA")]
    for e in els:
        for k in list(e["faces"]):
            if k == "south":
                del e["faces"][k]
    els = [e for e in els if e["faces"]]
    return P.mirror_x(els) if hand == "stbd" else els


def doorhead():
    """Over a door: inside, the curved panel and the lit EXIT sign; outside (south), the skin and the canopy's top."""
    return [B("Curve", (0, 0, 1.5), (16, 16.6, 3), "c-panel", faces=("north",), rot=(22.5, 0, 0), origin=(8, 0, 1.5)),
            B("Top", (0, 15.2, -4.9), (16, 16, 1.5), "c-ceil", faces=("down",)),
            pic(B("Exit", (4, 2.5, -0.4), (12, 6.5, 1.2), "c-dark", faces=("up", "down", "east", "west")), "north", "sign-exit", glow=255),
            B("Skin", (0, 0, 15), (16, 16, 16), "skin", faces=("south",)),
            B("Canopy", (-0.5, 9, 16), (16.5, 16, 20), "canopy", faces=("south", "down")),
            B("CanopyRib", (-0.5, 8.4, 16), (16.5, 9, 20.4), "rubber", faces=("south", "down"))]


def doorside(which, part):
    """The fuselage beside the boarding door (fwd: the door at +x; aft: the door at -x). Inside, the sidewall (the
    attendant's panel forward, a placard aft); outside (south, toward the bridge), the white skin, the cheatline at window
    height and the canopy's bellows along the bridge's side."""
    inside = {"low": side_lower(), "mid": side_plain(), "top": side_upper()}[part]
    els = renamed(inside, "In")
    if part == "mid" and which == "fwd":
        els += [pic(B("Attendant", (3, 3, 0.8), (13, 13, 1.5), "c-grey", faces=("up", "down", "east", "west")), "north", "panel-attendant")]
    if part == "mid" and which == "aft":
        els += [pic(B("Safety", (4, 4, 1.2), (12, 12, 1.5), "c-grey", faces=("up", "down", "east", "west")), "north", "placard-safety")]
    els.append(B("Skin", (0, 0, 15), (16, 16, 16), {"mid": "c-skinband", "low": "c-skinpin"}.get(part, "skin"), faces=("south",)))
    x0, x1 = (-0.5, 4) if which == "fwd" else (12, 16.5)
    els += [B("Bellows", (x0, 0, 16), (x1, 16, 20), "canopy", faces=("south", "east", "west")),
            B("Rib", (x0, 0, 16), (x1, 16, 20.4), "rubber", faces=("south",))]
    els[-1]["from"][0] = (x1 - 0.6) if which == "fwd" else x0
    els[-1]["to"][0] = x1 if which == "fwd" else x0 + 0.6
    if part == "top":
        els += [B("CanopyTop", (-0.5, 9, 16), (16.5, 16, 20), "canopy", faces=("south", "down"))]
    return els


def cabinexit(part):
    """An overwing exit hatch in the sidewall: lower (the panel and the hatch's foot), upper (the hatch with its window,
    blind down, the red pull handle, the lit EXIT sign over it)."""
    if part == "lower":
        return [B("Panel", (0, 0, 1.5), (16, 6, 16), "c-panel", faces=("north", "up")),
                B("Kick", (0, 0, 0.75), (16, 1.5, 16), "c-grey", faces=("north", "up")),
                B("Hatch", (1.5, 6, 1), (14.5, 16, 16), "c-panel", faces=("north",)),
                B("SealL", (1.2, 6, 0.8), (1.5, 16, 1.6), "c-grey", faces=("north", "west")),
                B("SealR", (14.5, 6, 0.8), (14.8, 16, 1.6), "c-grey", faces=("north", "east")),
                B("SealB", (1.2, 5.7, 0.8), (14.8, 6, 1.6), "c-grey", faces=("north", "down")),
                B("SideL", (0, 6, 1.5), (1.2, 16, 16), "c-panel", faces=("north",)),
                B("SideR", (14.8, 6, 1.5), (16, 16, 16), "c-panel", faces=("north",))]
    els = [e for e in shift(porthole(shut=True), dy=-2) if e["name"] not in ("PlL", "PlR", "PlT", "PlB")]
    els += [B("PlL", (1.5, 0, 1), (4.75, 12, 16), "c-panel", faces=("north", "east")),
            B("PlR", (11.25, 0, 1), (14.5, 12, 16), "c-panel", faces=("north", "west")),
            B("PlT", (4.75, 11, 1), (11.25, 12, 16), "c-panel", faces=("north", "down")),
            B("PlB", (4.75, 0, 1), (11.25, 2, 16), "c-panel", faces=("north", "up")),
            B("SealL", (1.2, 0, 0.8), (1.5, 12, 1.6), "c-grey", faces=("north", "west")),
            B("SealR", (14.5, 0, 0.8), (14.8, 12, 1.6), "c-grey", faces=("north", "east")),
            B("SealT", (1.2, 12, 0.8), (14.8, 12.3, 1.6), "c-grey", faces=("north", "up")),
            B("SideL", (0, 0, 1.5), (1.2, 16, 16), "c-panel", faces=("north",)),
            B("SideR", (14.8, 0, 1.5), (16, 16, 16), "c-panel", faces=("north",)),
            B("Above", (1.2, 12.3, 1.5), (14.8, 16, 16), "c-panel", faces=("north",)),
            B("Pull", (5, 9.4, 0.1), (11, 10.4, 1), "c-red", faces=no("south")),
            pic(B("Exit", (4.5, 13, 0.9), (11.5, 15.4, 1.5), "c-dark", faces=("up", "down", "east", "west")), "north", "sign-exit", glow=255)]
    return els


# ======================================================================== The nose and the rear

def bulkhead(part):
    """The forward bulkhead's face toward the cabin: low (kick and panel), mid (the safety placard), midext (an
    extinguisher in its bracket), top (curving into the ceiling)."""
    if part == "low":
        return [B("Panel", (0, 1.5, 0.5), (16, 16, 16), "c-panel", faces=("north",)),
                B("Kick", (0, 0, 0), (16, 1.5, 16), "c-grey", faces=("north", "up"))]
    if part == "top":
        return [B("Panel", (0, 0, 0.5), (16, 12, 16), "c-panel", faces=("north",)),
                B("Cove", (0, 12, 0.5), (16, 16, 3), "c-ceil", faces=("north", "down"), rot=(30, 0, 0), origin=(8, 12, 0.5))]
    els = [B("Panel", (0, 0, 0.5), (16, 16, 16), "c-panel", faces=("north",))]
    if part == "mid":
        els.append(pic(B("Safety", (3, 2, 0.2), (13, 12, 0.5), "c-grey", faces=("up", "down", "east", "west")), "north", "placard-safety"))
    else:
        els += [B("Bracket", (5.5, 1, 0.1), (10.5, 2, 0.5), "darksteel", faces=no("south")),
                B("Bottle", (6.5, 2, -2.6), (9.5, 10.5, 0.4), "c-red", faces=no("south", "down")),
                B("Neck", (7.2, 10.5, -1.9), (8.8, 11.5, -0.3), "darksteel", faces=no("south", "down")),
                B("Lever", (7, 11.5, -2.2), (10.5, 12, -0.3), "chrome", faces=no("south")),
                B("Hose", (9.5, 7, -1.4), (10.2, 11, -0.6), "black", faces=no("south")),
                B("Strap", (6.3, 6, -2.8), (9.7, 6.8, 0.4), "darksteel", faces=no("south", "down", "up")),
                pic(B("Label", (6.6, 4, -2.7), (9.4, 6, -2.6), "c-trim", faces=()), "north", "placard-flightdeck", (0, 0, 16, 16))]
        els[-1]["faces"]["north"]["texture"] = "#c-trim"
    return els


def fddoor(part):
    """The flight deck's door in the forward bulkhead: a reinforced grey door in its frame; lower (the kick plate, the
    decompression louvre), upper (the lever, the keypad on the frame, the peephole, the FLIGHT DECK placard)."""
    els = [B("FrameL", (0, 0, -0.5), (1.5, 16, 16), "c-trim", faces=("north", "east")),
           B("FrameR", (14.5, 0, -0.5), (16, 16, 16), "c-trim", faces=("north", "west")),
           B("Leaf", (1.5, 0, 0.5), (14.5, 16, 16), "c-fddoor", faces=("north",))]
    if part == "lower":
        els += [B("Kick", (1.5, 0, 0.2), (14.5, 2, 0.5), "steel", faces=("north", "up")),
                B("Louvre", (3, 3, 0.3), (13, 8, 0.5), "c-louvre", faces=("north",), uv=(0, 0, 16, 16)),
                B("Seam", (1.5, 15.6, 0.3), (14.5, 16, 0.5), "c-grey", faces=("north",))]
    else:
        els += [B("FrameT", (0, 14, -0.5), (16, 16, 16), "c-trim", faces=("north", "down")),
                B("Lever", (2.5, 0.2, -1.2), (6.5, 1.0, 0.5), "chrome", faces=no("south")),
                B("LeverHub", (2.4, -0.4, -0.6), (3.6, 1.4, 0.5), "chrome", faces=no("south")),
                B("Peep", (7.4, 7.4, 0.1), (8.6, 8.6, 0.5), "chrome", faces=no("south")),
                B("PeepGlass", (7.7, 7.7, 0.05), (8.3, 8.3, 0.1), "black", faces=("north",)),
                pic(B("Placard", (3.5, 10.5, 0.2), (12.5, 12.5, 0.5), "c-dark", faces=("up", "down", "east", "west")), "north", "placard-flightdeck"),
                B("Keypad", (14.7, 3, -1), (15.9, 7, -0.5), "c-dark", faces=no("south")),
                B("Keys", (14.85, 3.4, -1.1), (15.75, 6.2, -1), "c-grey", faces=("north",)),
                B("KeyLed", (15.1, 6.4, -1.1), (15.5, 6.8, -1), "c-led", faces=("north",), glow=200)]
        els[-1]["faces"]["north"]["texture"] = "#c-red"
    return els


GALLEY_FRAME = "steel"


def galley(part):
    """A galley unit's block, facing the aisle: carts / cartswaste (two half-size carts in their bay, or a cart and the
    waste flap), oven / coffee / counter (the worktop, the units over it), stow (a row of standard containers, a work
    light under them)."""
    els = [B("PostL", (0, 0, 0), (0.6, 16, 16), GALLEY_FRAME, faces=("north", "west", "east")),
           B("PostR", (15.4, 0, 0), (16, 16, 16), GALLEY_FRAME, faces=("north", "east", "west")),
           B("Back", (0.6, 0, 15), (15.4, 16, 16), "c-grey", faces=("north",))]
    if part in ("carts", "cartswaste"):
        els += [pic(B("CartA", (0.9, 0.3, 1.2), (7.8, 15, 15), GALLEY_FRAME, faces=("up", "east", "west")), "north", "galley-cart"),
                B("Kick", (0.6, 0, 0.3), (15.4, 0.3, 15), "black", faces=("north", "up")),
                B("Lip", (0.6, 15, 0.3), (15.4, 16, 15), "steel", faces=("north", "down")),
                B("LatchA", (3.3, 13.2, 0.7), (5.4, 14.0, 1.2), "c-red", faces=no("south"))]
        if part == "carts":
            els += [pic(B("CartB", (8.2, 0.3, 1.2), (15.1, 15, 15), GALLEY_FRAME, faces=("up", "east", "west")), "north", "galley-cart"),
                    B("LatchB", (10.6, 13.2, 0.7), (12.7, 14.0, 1.2), "c-red", faces=no("south"))]
        else:
            els += [pic(B("Waste", (8.2, 0.3, 0.8), (15.1, 15, 15), GALLEY_FRAME, faces=("up", "east", "west")), "north", "galley-waste")]
        return els
    if part == "stow":
        els += [pic(B("Stow", (0.6, 1.2, 0.8), (15.4, 8, 15), GALLEY_FRAME, faces=("down",)), "north", "galley-stow"),
                pic(B("Stow2", (0.6, 8.3, 0.8), (15.4, 15.1, 15), GALLEY_FRAME, faces=()), "north", "galley-stow"),
                B("Top", (0, 15.1, 0), (16, 16, 16), "c-trim", faces=("north", "down")),
                B("Work", (1, 0.6, 1), (15, 1.2, 2.2), "c-led", faces=("down", "north"), glow=180),
                B("WorkHood", (0.6, 1.2, 0.6), (15.4, 1.5, 3), "steel", faces=("north", "down"))]
        return els
    els += [B("Worktop", (0, 0, 0), (16, 1, 16), "steel", faces=("north", "up")),
            B("Splash", (0.6, 1, 14.5), (15.4, 4, 15), "steel", faces=("north",))]
    if part == "oven":
        els += [pic(B("Oven", (1.2, 4, 3), (14.8, 15.6, 15), GALLEY_FRAME, faces=("down", "east", "west", "up")), "north", "galley-oven"),
                B("OvenHandle", (2.5, 13.6, 2.2), (11.5, 14.2, 3), "chrome", faces=no("south")),
                B("Pot", (2, 1, 5), (5, 4, 8), "black", faces=no("down")),
                B("Cups", (11, 1, 3), (13, 3.5, 5), "white", faces=no("down"))]
    elif part == "coffee":
        els += [pic(B("BrewA", (1.2, 4, 4), (7.8, 15.6, 15), GALLEY_FRAME, faces=("down", "east", "west", "up")), "north", "galley-coffee"),
                pic(B("BrewB", (8.2, 4, 4), (14.8, 15.6, 15), GALLEY_FRAME, faces=("down", "east", "west", "up")), "north", "galley-coffee"),
                B("PotA", (2.6, 1, 1.8), (5.6, 4.6, 4.6), "c-glass", faces=no("down")),
                B("CoffeeA", (2.7, 1, 1.9), (5.5, 3, 4.5), "c-coffee", faces=("north", "east", "west")),
                B("PotAH", (5.6, 2.4, 2.8), (6.4, 4.2, 3.6), "black", faces=no("down")),
                B("PotALid", (2.8, 4.6, 2.0), (5.4, 5.1, 4.4), "black", faces=no("down"))]
    else:
        els += [B("Shelf", (0.6, 8, 3), (15.4, 8.6, 15), "steel", faces=("north", "up", "down")),
                B("Back2", (0.6, 4, 14.4), (15.4, 15.6, 14.6), "c-grey", faces=("north",)),
                B("CupStack", (1.8, 1, 2), (3.6, 6, 3.8), "white", faces=no("down")),
                B("CupStack2", (4, 1, 2.4), (5.8, 5.2, 4.2), "white", faces=no("down")),
                B("Tray", (8, 1, 2), (14, 1.4, 9), "darkplastic", faces=no("down")),
                B("Pot", (9.5, 1.4, 3.5), (12, 4.6, 6), "c-glass", faces=no("down")),
                B("PotCoffee", (9.6, 1.4, 3.6), (11.9, 3.2, 5.9), "c-coffee", faces=("north", "east", "west")),
                B("PotLid", (9.7, 4.6, 3.7), (11.8, 5, 5.8), "black", faces=no("down")),
                B("Napkins", (2, 8.6, 5), (6, 10.4, 10), "white", faces=no("down")),
                B("Boxes", (8, 8.6, 6), (14, 12.6, 13), "c-trim", faces=no("down")),
                pic(B("Stow", (0.6, 12.8, 0.8), (15.4, 15.6, 15), GALLEY_FRAME, faces=("down",)), "north", "galley-stow", (0, 0, 16, 8))]
    return els


def lav(part):
    """A lavatory module, its door toward the aisle: doorlow (the bifold door's lower half, its louvre), doorocc / doorvac
    (the upper half with the latch's OCCUPIED / VACANT indicator), top (over the door, the lit lavatory sign), body (a
    plain side of the module)."""
    frame = [B("FrameL", (0, 0, 0), (1, 16, 16), "c-trim", faces=("north", "east", "west")),
             B("FrameR", (15, 0, 0), (16, 16, 16), "c-trim", faces=("north", "east", "west"))]
    if part == "body":
        return [B("Body", (0, 0, 0), (16, 16, 16), "c-panel", faces=DIRS),
                B("Seam", (7.8, 0, -0.1), (8.2, 16, 0), "c-trim", faces=("north",))]
    if part == "top":
        return frame + [B("Panel", (1, 0, 0.5), (15, 16, 16), "c-panel", faces=("north", "down")),
                        B("Head", (0, 0, 0), (16, 1, 16), "c-trim", faces=("north", "down")),
                        pic(B("Sign", (4, 5, -0.4), (12, 9, 0.5), "c-dark", faces=("up", "down", "east", "west")), "north", "sign-lav", glow=180)]
    els = frame + [B("LeafA", (1, 0, 1.2), (8, 16, 16), "c-panel", faces=("north", "up", "down")),
                   B("LeafB", (8, 0, 1.0), (15, 16, 16), "c-panel", faces=("north", "up", "down", "west")),
                   B("Fold", (7.8, 0, 0.9), (8.2, 16, 1.2), "c-trim", faces=("north", "east", "west"))]
    if part == "doorlow":
        els += [B("Louvre", (2.5, 1.5, 0.95), (6.5, 6, 1.2), "c-louvre", faces=("north",), uv=(0, 0, 16, 16)),
                B("Kick", (0, 0, -0.1), (16, 1, 1), "c-grey", faces=("north", "up"))]
    else:
        ind = "ind-occupied" if part == "doorocc" else "ind-vacant"
        els += [B("Pull", (12.5, 0, 0.2), (13.5, 5, 1), "chrome", faces=no("south")),
                B("Latch", (10.8, 6.5, 0.4), (14.2, 8.7, 1), "c-dark", faces=("up", "down", "east", "west")),
                pic(B("Ind", (11.1, 6.8, 0.3), (13.9, 8.3, 0.4), "c-dark", faces=()), "north", ind, glow=200),
                B("Ash", (3, 3, 0.5), (6, 5, 1.2), "steel", faces=no("south")),
                B("Head", (0, 15, 0), (16, 16, 16), "c-trim", faces=("north", "down"))]
        els[-4]["faces"]["north"] = {"texture": "#c-dark", "uv": [0, 0, 16, 16]}
    return els


def jumpseat():
    """The cabin crew's jump seat, folded against the lavatory's side (the back of the block), facing the door's row: its
    frame, the folded pan, the back cushion and headrest, the shoulder harness."""
    els = [B("Frame", (2.5, 1, 15.2), (13.5, 30, 16), "c-grey", faces=("north", "east", "west", "up")),
           B("Back", (3, 8, 13.8), (13, 25, 15.2), "cabin-side", faces=no("south")),
           B("Head", (4, 25.5, 13.6), (12, 29.5, 15.2), "cabin-side", faces=no("south")),
           B("Pan", (3, 9, 11.4), (13, 19, 13.4), "darkplastic", faces=no("south")),
           B("PanPad", (3.4, 9.4, 11.1), (12.6, 18.6, 11.4), "cabin", faces=("north",)),
           B("Hinge", (2.8, 8.4, 12), (13.2, 9.2, 14), "steel", faces=no("south")),
           B("StrapL", (4.6, 9, 11.0), (5.8, 26, 11.2), "webgrey", faces=("north",)),
           B("StrapR", (10.2, 9, 11.0), (11.4, 26, 11.2), "webgrey", faces=("north",)),
           B("Buckle", (7, 14, 10.8), (9, 16, 11.1), "chrome", faces=no("south")),
           pic(B("Placard", (5, 3, 15.0), (11, 6, 15.2), "c-trim", faces=()), "north", "placard-lifevest", (0, 0, 16, 16))]
    return els


def curtain(part):
    """The galley's curtain on its rail, drawn half across (from the galley's side, -x), in pleats."""
    els = []
    y0, y1 = {"lower": (1, 16), "mid": (0, 16), "top": (0, 15)}[part]
    for i in range(5):
        x = 0.2 + i * 2
        z = 0.6 if i % 2 == 0 else 1.6
        els.append(B(f"Pleat{i}", (x, y0, z), (x + 2.2, y1, z + 0.6), "curtain", faces=("north", "south", "east", "west", "down"),
                     uv=(i * 3, 0, i * 3 + 3, 16)))
    if part == "top":
        els += [B("Rail", (0, 15, 0.8), (16, 15.6, 1.6), "chrome", faces=("north", "south", "down", "east")),
                B("Track", (0, 15.6, 0.6), (16, 16, 1.8), "c-trim", faces=("north", "south", "down"))]
    return els


# ======================================================================== Floors

def aisle_floor():
    """The aisle's carpet with the floor-path light strips along both its edges (glowing: they stay lit when the cabin's
    lights are down), running along z."""
    return [B("Carpet", (0, 0, 0), (16, 15.9, 16), "c-aisle", faces=DIRS),
            B("StripW", (1.2, 15.9, 0), (1.8, 16.05, 16), "c-strip", faces=("up", "east", "west"), glow=200),
            B("StripE", (14.2, 15.9, 0), (14.8, 16.05, 16), "c-strip", faces=("up", "east", "west"), glow=200),
            B("EdgeW", (0.9, 15.9, 0), (2.1, 15.95, 16), "c-grey", faces=("up",)),
            B("EdgeE", (13.9, 15.9, 0), (15.1, 15.95, 16), "c-grey", faces=("up",))]


# ======================================================================== Block types

STRUCT = {"attributes": {"l36structure": True}}
FULL = [(0, 0, 0, 1, 1, 1)]


def cube_block(code, groups, textures, comment, extra=None):
    import gen_36_surfaces as GS
    data = {"variantgroups": groups, "texturesByType" if groups else "textures": textures, "blockmaterial": "Stone",
            "drawtype": "cube", "lightAbsorption": 99, "resistance": 6, "sounds": GS.STONE, "attributes": dict(GS.STRUCT)}
    if not groups:
        data.pop("variantgroups")
    data.update(extra or {})
    GS.block(code, comment, data)


def blocks():
    side = [("side", SIDES)]
    blk = P.block
    blk("l36-cabinwindow", [("phase", PHASES)] + side, lambda v: porthole(view="view-" + v["phase"], glow=PHASE_GLOW[v["phase"]]),
        "Level 36 (cabin pass): the cabin's sidewall with its porthole facing the cabin (<side>): the reveal, a raised bezel, the "
        "blind up, the pane's picture by the flight's phase (apron: parked at the gate; roll: the runway rushing past; climb: the "
        "ground falling away under a wing tip; cruise: cloud tops and a low sun; descent: grey cloud and rain; ground: the "
        "taxiway's lights at dusk), glowing, a little daylight through it; the flight's logic swaps them", boxes=FULL, material="Stone",
        sounds=P.STONE, data={"lightHsvByType": {f"*-{k}-*": [36, 1, v] for k, v in PHASE_LIGHT.items() if v}, **STRUCT})
    blk("l36-cabinblind", side, lambda v: porthole(shut=True),
        "Level 36 (cabin pass): a cabin window with its blind pulled down", boxes=FULL, material="Stone", sounds=P.STONE, data=STRUCT)
    blk("l36-cabinside", [("part", ("lower", "plain", "upper"))] + side,
        lambda v: {"lower": side_lower, "plain": side_plain, "upper": side_upper}[v["part"]](),
        "Level 36 (cabin pass): the cabin's sidewall (lower: the dado with its air grille; plain: between the windows; upper: "
        "curving in toward the bins)", boxes=FULL, material="Stone", sounds=P.STONE, data=STRUCT)
    blk("l36-psu", [("state", ("off", "on"))] + side, lambda v: psu(v["state"] == "on"),
        "Level 36 (cabin pass): the passenger service unit under an overhead bin, toward the aisle: reading lights, air nozzles, "
        "the call button, the FASTEN SEAT BELT / NO SMOKING sign (off: dark; on: lit, from the doors closing to the landing)",
        boxes=[(0, 0.03, 0, 1, 1, 1)], material="Stone", sounds=P.STONE, data=STRUCT)
    bins = tuple(f"r{n}" for n in ROWS) + ("openbag", "opencoat")
    blk("l36-cabinbin", [("state", bins)] + side, lambda v: bin_block(v["state"]),
        "Level 36 (cabin pass): an overhead bin over the aisle seat, its door toward the aisle (<side>): the row's number on its lip "
        "(10 to 18, no 13), the ceiling's cove rising from its top; open with a bag in it, or a coat's sleeve hanging out",
        boxes=[(0, 0.03, 0, 1, 1, 1)], material="Stone", sounds=P.STONE, data=STRUCT)
    blk("l36-cabinsign", side, lambda v: exit_sign(),
        "Level 36 (cabin pass): an EXIT sign hung over the aisle, lit on both faces", boxes=None,
        sel=[(0.18, 0.55, 0.4, 0.82, 1, 0.6)], material="Metal", sounds=P.METAL, data=STRUCT)
    for kind in ("plain",) + ("blanket", "pillow", "bag", "magazine", "exitrow"):
        pass
    seat_boxes = [(0.03, 0, 0.06, 0.97, 0.56, 0.8), (0.06, 0, 0.72, 0.94, 1.5, 0.95)]
    blk("l36-cabinseat", side, lambda v: seat(),
        "Level 36's plane cabin: an economy seat (navy cloth, a white headrest cover, armrests shared with the next seat, the tray "
        "and its latch, the pocket with the safety card and the in-flight magazine, the life-vest pouch, the belt buckled across); "
        "side = the way a sitter faces", boxes=seat_boxes, sel=[(0.03, 0, 0.06, 0.97, 1.5, 0.95)], material="Cloth", sounds=P.CLOTH)
    blk("l36-cabinseat2", [("kind", ("blanket", "pillow", "bag", "magazine", "exitrow"))] + side, lambda v: seat(v["kind"]),
        "Level 36's plane cabin: an economy seat with something left behind (a folded blanket, a pillow, a backpack under it, the "
        "magazine dropped on the floor) or an exit row's seat with its placard (decor: nothing in them)", boxes=seat_boxes,
        sel=[(0.03, 0, 0.06, 0.97, 1.5, 0.95)], material="Cloth", sounds=P.CLOTH)
    door_boxes = lambda v: None if v["state"] == "open" else FULL
    blk("l36-planedoor", [("state", ("open", "closed")), ("part", ("lower", "upper"))] + side, lambda v: planedoor(v["state"], v["part"]),
        "Level 36 (cabin pass): the plane's boarding door (L1) where the jet bridge ends, two blocks high (lower / upper), facing "
        "the cabin: its frame, sill and assist handle; open, the leaf swung forward against the skin with its slide bustle showing "
        "(walk through); closed, the leaf in the frame (the flight's logic closes it at departure)", boxes=door_boxes,
        sel=lambda v: [(0, 0, 0.1, 1, 1, 1)], material="Metal", sounds=P.METAL, data=STRUCT)
    blk("l36-doorhead", side, lambda v: doorhead(),
        "Level 36 (cabin pass): over a plane door: the lit EXIT sign inside, the fuselage's skin and the bridge's canopy outside",
        boxes=FULL, material="Metal", sounds=P.METAL, data=STRUCT)
    blk("l36-doorside", [("part", ("fwdlow", "fwdmid", "fwdtop", "aftlow", "aftmid", "afttop"))] + side,
        lambda v: doorside(v["part"][:3], v["part"][3:]),
        "Level 36 (cabin pass): the fuselage beside the boarding door: the cabin's sidewall inside (the crew's panel forward, a "
        "safety placard aft), the white skin with the airline's cheatline and the jet bridge's canopy outside", boxes=FULL,
        material="Metal", sounds=P.METAL, data=STRUCT)
    blk("l36-cabindoor", [("hand", ("port", "stbd")), ("part", ("lower", "upper"))] + side, lambda v: cabindoor(v["hand"], v["part"]),
        "Level 36 (cabin pass): a closed plane door seen from inside (R1, L2, R2): the lining, the handle, the viewport, the slide "
        "bustle", boxes=FULL, material="Metal", sounds=P.METAL, data=STRUCT)
    blk("l36-cabinexit", [("part", ("lower", "upper"))] + side, lambda v: cabinexit(v["part"]),
        "Level 36 (cabin pass): an overwing exit hatch in the sidewall (its window's blind down, the red pull handle, the lit EXIT "
        "sign over it)", boxes=FULL, material="Stone", sounds=P.STONE, data=STRUCT)
    blk("l36-bulkhead", [("part", ("low", "mid", "midext", "top"))] + side, lambda v: bulkhead(v["part"]),
        "Level 36 (cabin pass): the forward bulkhead (low; mid with the safety placard; midext with a fire extinguisher; top)",
        boxes=FULL, material="Stone", sounds=P.STONE, data=STRUCT)
    blk("l36-fddoor", [("part", ("lower", "upper"))] + side, lambda v: fddoor(v["part"]),
        "Level 36 (cabin pass): the flight deck's door, locked (a reinforced grey door, the lever, the keypad, the peephole, the "
        "FLIGHT DECK placard); nobody answers", boxes=FULL, material="Metal", sounds=P.METAL, data=STRUCT)
    blk("l36-galley", [("part", ("carts", "cartswaste", "oven", "coffee", "counter", "stow"))] + side, lambda v: galley(v["part"]),
        "Level 36 (cabin pass): a galley unit (carts: two trolleys in their bay; cartswaste: a trolley and the waste flap; oven; "
        "coffee: two beverage makers and a pot; counter: cups, a tray, a pot; stow: standard containers and the work light)",
        boxes=FULL, material="Metal", sounds=P.METAL, data={"lightHsvByType": {"*-stow-*": [8, 1, 5]}, **STRUCT})
    blk("l36-lav", [("part", ("doorlow", "doorocc", "doorvac", "top", "body"))] + side, lambda v: lav(v["part"]),
        "Level 36 (cabin pass): a lavatory module (its bifold door, lower and upper with the OCCUPIED or VACANT latch; the lit sign "
        "over it; a plain side); the door does not open", boxes=FULL, material="Stone", sounds=P.STONE, data=STRUCT)
    blk("l36-jumpseat", side, lambda v: jumpseat(),
        "Level 36 (cabin pass): the cabin crew's jump seat, folded against the lavatory", boxes=[(0.15, 0, 0.7, 0.85, 1, 1)],
        material="Cloth", sounds=P.CLOTH)
    blk("l36-curtain", [("part", ("lower", "mid", "top"))] + side, lambda v: curtain(v["part"]),
        "Level 36 (cabin pass): the galley's curtain on its rail, drawn half across", boxes=None,
        sel=[(0, 0, 0, 0.65, 1, 0.2)], material="Cloth", sounds=P.CLOTH)
    blk("l36-cabinfloor", [("kind", ("aisle",)), ("axis", ("ns", "we"))], lambda v: aisle_floor() if v["axis"] == "ns" else MK.turn(aisle_floor(), 1),
        "Level 36 (cabin pass): the cabin's aisle carpet with its floor-path light strips (axis: the way the aisle runs)",
        boxes=FULL, rot="none", material="Cloth", sounds=P.CLOTH, data={"lightHsv": [6, 4, 4], **STRUCT})
    # (the track carpet and the vinyl are cubes)
    tex = lambda n: {"base": "backrooms:block/36/cabin/" + n}
    cube_block("l36-cabinfloor-track", [{"code": "axis", "states": ["ns", "we"]}],
               {"*-ns": {"all": tex("c-track-ns")}, "*-we": {"all": tex("c-track-we")}},
               "Level 36 (cabin pass): the cabin's carpet with the seats' aluminium tracks in it", extra={"sounds": P.CLOTH})
    cube_block("l36-cabinfloor-plain", [], {"all": tex("c-carpet")}, "Level 36 (cabin pass): the cabin's carpet in the door rows",
               extra={"sounds": P.CLOTH})
    cube_block("l36-cabinfloor-vinyl", [], {"all": tex("c-vinyl")}, "Level 36 (cabin pass): the galleys' grey non-slip vinyl")
    cube_block("l36-ceiling-cabin", [], {"all": {"base": "backrooms:block/36/l36-ceiling-cabin"}},
               "Level 36 (cabin pass): the cabin's lit ceiling over the aisle and the door rows (it gives the cabin its light; it "
               "was a state of l36-ceiling)", extra={"lightHsv": [8, 1, 22], "blockmaterial": "Metal", "vertexFlags": {"glowLevel": 120}})
    cube_block("l36-ceiling-cabin-dim", [], {"all": {"base": "backrooms:block/36/l36-ceiling-cabin-dim"}},
               "Level 36 (cabin pass): the cabin's ceiling over the aisle with its lights down for takeoff and landing (night blue)",
               extra={"lightHsv": [38, 3, 9], "blockmaterial": "Metal", "vertexFlags": {"glowLevel": 30}})


NAMES = {
    "block-l36-cabinwindow-*": "Cabin Window",
    "block-l36-cabinblind-*": "Cabin Window (Blind Down)",
    "block-l36-cabinside-*": "Cabin Sidewall",
    "block-l36-psu-*": "Passenger Service Unit",
    "block-l36-cabinbin-*": "Overhead Bin",
    "block-l36-cabinsign-*": "Cabin Exit Sign",
    "block-l36-cabinseat2-exitrow-*": "Economy Seat (Exit Row)",
    "block-l36-cabinseat2-*": "Economy Seat (Something Left Behind)",
    "block-l36-planedoor-*": "Plane Door",
    "block-l36-doorhead-*": "Door Header",
    "block-l36-doorside-*": "Fuselage",
    "block-l36-cabindoor-*": "Plane Door",
    "block-l36-cabinexit-*": "Overwing Exit",
    "block-l36-bulkhead-*": "Bulkhead",
    "block-l36-fddoor-*": "Flight Deck Door",
    "block-l36-galley-*": "Galley Unit",
    "block-l36-lav-*": "Lavatory",
    "block-l36-jumpseat-*": "Crew Jump Seat",
    "block-l36-curtain-*": "Galley Curtain",
    "block-l36-cabinfloor-aisle-*": "Cabin Aisle",
    "block-l36-cabinfloor-track-*": "Cabin Carpet",
    "block-l36-cabinfloor-vinyl": "Galley Floor",
    "block-l36-cabinfloor-plain": "Cabin Carpet",
    "block-l36-ceiling-cabin-dim": "Cabin Ceiling (Lights Down)",
}


def main():
    CT.textures()
    materials()
    SHAPE_FILES.clear()
    old_shape, P.shape = P.shape, shape
    try:
        P.CODES.clear()
        blocks()
    finally:
        P.shape = old_shape
    print(f"gen_36_cabin: {len(P.CODES) + 3} block types, {len(SHAPE_FILES)} shapes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
