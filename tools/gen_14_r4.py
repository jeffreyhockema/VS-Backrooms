"""Level 14 "The Hospital", round 4 (2026-11-02, the asset-quality pass): the models and textures rebuilt or added to
the bar of the released levels (docs/design/experimental-levels/14-plan.md, "Round 4"). Called from
tools/gen_14_props.py (props) and tools/gen_14.py (wall decorations, surfaces).

Every model faces north (its front toward -Z) as the rest of the level's props (tools/gen_14_props_kit.py); two-block
props are modelled 32 long (foot z 0-16, head z 16-32) and cut in halves. Texture keys are p-* (props) in
textures/block/14/.

New props
    l14-gurney-{head|foot}-{plain|strap}-{side}   a stretcher trolley two blocks long (from Level !'s run-gurney, re-detailed
                                    and rusted): castors on forks, a base frame, two hydraulic columns in bellows, the deck,
                                    the mattress with its back rest raised, a rumpled sheet, one side rail up and one down, a
                                    push bar. strap: restraint straps and blood (the torture chambers)
    l14-wheelchair-{side}           a hospital wheelchair facing <side> (from Level !'s run-wheelchair): spoked wheels with
                                    push rims, front castors, a sling seat and back, arm pads, footplates (one folded)
    l14-ivstand-{side}              a drip stand: a five-castor base, the pole and its hook crown, a saline bag and its line
                                    to an infusion pump clamped on the pole, its panel toward <side>
    l14-stationback-{lower|upper}-{board|files}-{side}   the nurses' station's back wall unit, two blocks: a cupboard and
                                    pigeonholes (lower), a whiteboard of names or a chart rack (upper), front to <side>
Rebuilt
    l14-surglamp (a ceiling mount, a drop tube, two arms with spring housings, two lamp heads in yokes, lit lenses),
    l14-optable (one table over two blocks on a column at the joint), l14-stretchers (tubular steel stretchers)
"""
import math
import random

from PIL import Image, ImageDraw

import matlib as M
import gen_14_props_tex as TX
from gen_14_props_kit import B, no, pic, glow, turned, transparent, rename, octagon, rod, move, turn, clip_z
from gen_14_props_a import castor, five_star

S = 32
RUST, RUSTDARK, BLOOD = TX.RUST, TX.RUSTDARK, TX.BLOOD


# ======================================================================== Textures

def textures():
    sd = TX.seed_of
    # Black cracked vinyl (the wheelchair's sling and arm pads)
    img = M.noise_hv((44, 44, 46), 2, sd("sling"), S, mottle=3, hue=0.4)
    M.emboss_lines(img, ys=(0, 16), strength=0.12)
    M.scratches(img, 6, seed=sd("slingS"), light=0.16)
    rng = random.Random(sd("slingC"))
    px = img.load()
    for _ in range(9):
        x, y = rng.randrange(S), rng.randrange(S)
        for k in range(rng.randint(2, 5)):
            px[(x + k) % S, (y + rng.choice((0, 0, 1))) % S] = TX.rgba((150, 140, 120))
    M.grime(img, 0.12, seed=sd("slingG"), color=(90, 80, 60))
    TX.save(img, "sling")
    # A tubular frame: chrome gone dull, rust blooming at the joints and in scratches
    img = M.brushed_metal(seed=sd("tubes"), base=(178, 182, 186), direction="h", streak=5, sheen=10)
    M.rust(img, 0.16, seed=sd("tubesR"), color=RUST, dark=RUSTDARK, pits=True, cells=(8, 4))
    M.grime(img, 0.12, seed=sd("tubesG"), color=(80, 70, 56))
    TX.save(img, "tubes")
    # The stretchers' pads: grey-green vinyl, split, stained with rust and old blood
    img = M.noise_hv((92, 104, 92), 3, sd("stretchpad"), S, mottle=6, hue=1)
    M.emboss_lines(img, ys=(15,), strength=0.18)
    M.stain(img, seed=sd("stretchpadS"), radius=9, color=(70, 44, 26), strength=0.45, at=(10, 20))
    TX.blood(img, sd("stretchpadB"), 6, (1, 3))
    M.grime(img, 0.25, seed=sd("stretchpadG"), color=(52, 46, 36))
    TX.save(img, "stretchpad")
    # Bellows (rubber boots on the gurney's columns): ribbed
    img = M.rubber(seed=sd("bellows"), base=(52, 52, 54))
    M.emboss_lines(img, ys=tuple(range(0, S, 4)), raised=True, strength=0.3)
    TX.save(img, "bellows")
    # A saline bag: clear plastic (translucent pass), the printed label and the scale
    img = Image.new("RGBA", (S, S), (220, 232, 236, 120))
    d = ImageDraw.Draw(img)
    d.rectangle([7, 8, 24, 22], fill=(240, 244, 246, 230))
    d.rectangle([7, 8, 24, 11], fill=(40, 90, 160, 255))
    for i, y in enumerate(range(13, 21, 2)):
        d.line([9, y, 9 + (6 if i % 2 else 11), y], fill=(40, 60, 90, 255))
    d.line([3, 4, 3, 28], fill=(250, 252, 255, 200))
    for y in range(6, 28, 4):
        d.line([26, y, 28, y], fill=(30, 40, 60, 220))
    TX.save(img, "saline")
    # The infusion pump's face: a dead LCD, the keypad, the door over the line, a sticker with a name
    img, d = TX.pic((S, S), (204, 206, 200))
    img = M.noise_hv((204, 206, 200), 1.5, sd("pump"), S, mottle=2)
    d = ImageDraw.Draw(img)
    d.rectangle([3, 3, 18, 11], fill=(36, 44, 40, 255))
    d.rectangle([4, 4, 17, 10], fill=(62, 74, 64, 255))
    d.line([5, 6, 11, 6], fill=(80, 96, 82, 255))
    for r in range(3):
        for c in range(3):
            d.rectangle([4 + c * 5, 14 + r * 5, 7 + c * 5, 17 + r * 5], fill=(150, 154, 156, 255))
    d.rectangle([21, 3, 28, 28], fill=(176, 180, 176, 255))
    d.line([24, 4, 24, 27], fill=(120, 130, 140, 255))
    d.rectangle([21, 29, 28, 30], fill=(196, 60, 50, 255))
    M.grime(img, 0.12, seed=sd("pumpG"), color=(120, 110, 90))
    TX.save(img, "pump")
    # The nurses' station back unit: the whiteboard of names (32 x 32 over a 16-unit face), the chart rack's spines,
    # the pigeonholes
    img = M.noise_hv((236, 238, 234), 1.2, sd("namesboard"), S, mottle=2)
    d = ImageDraw.Draw(img)
    d.line([0, 6, 31, 6], fill=(60, 80, 140, 255))
    for x in (8, 20):
        d.line([x, 0, x, 31], fill=(150, 160, 170, 255))
    rng = random.Random(sd("namesboardT"))
    for y in range(9, 31, 3):
        for x0, x1 in ((1, 7), (9, 19), (21, 30)):
            if rng.random() < 0.75:
                w = rng.randint(2, x1 - x0)
                col = rng.choice(((30, 40, 120), (30, 40, 120), (150, 30, 30), (30, 100, 50)))
                d.line([x0, y, x0 + w, y], fill=col + (255,))
    d.line([2, 2, 14, 2], fill=(30, 40, 120, 255))
    d.line([18, 2, 28, 2], fill=(150, 30, 30, 255))
    # ghosts of wiped names
    for _ in range(6):
        x, y = rng.randrange(2, 26), rng.randrange(8, 30)
        d.line([x, y, x + rng.randint(3, 6), y], fill=(214, 216, 214, 255))
    TX.save(img, "namesboard")
    img, d = TX.pic((S, S), (40, 40, 42))
    rng = random.Random(sd("binders"))
    x = 0
    while x < S:
        w = rng.choice((2, 3, 3, 4))
        c = rng.choice(((40, 70, 140), (150, 40, 36), (60, 110, 70), (200, 170, 60), (90, 90, 96), (226, 226, 220)))
        top = rng.randint(1, 4)
        d.rectangle([x, top, x + w - 1, 31], fill=c + (255,))
        d.rectangle([x, top + 4, x + w - 1, top + 6], fill=(236, 232, 214, 255))
        d.line([x + w - 1, top, x + w - 1, 31], fill=tuple(max(0, v - 30) for v in c) + (255,))
        x += w
    M.grime(img, 0.12, seed=sd("bindersG"), color=(60, 56, 48))
    TX.save(img, "binders")
    img, d = TX.pic((S, S), (60, 62, 60))
    for r in range(4):
        for c in range(4):
            x0, y0 = c * 8, r * 8
            d.rectangle([x0, y0, x0 + 7, y0 + 7], fill=(206, 208, 200, 255))
            d.rectangle([x0 + 1, y0 + 1, x0 + 6, y0 + 6], fill=(54, 54, 52, 255))
            if (r * 4 + c) % 3 != 1:
                d.rectangle([x0 + 1, y0 + 3, x0 + 6, y0 + 6], fill=(226, 222, 204, 255) if (r + c) % 2 else (200, 210, 226, 255))
            d.rectangle([x0 + 2, y0 + 7, x0 + 5, y0 + 7], fill=(240, 236, 210, 255))
    M.grime(img, 0.1, seed=sd("pigeonG"), color=(70, 64, 50))
    TX.save(img, "pigeonholes")
    # Lamp-head enamel for the surgical light: white with a faint yellowing and dust
    img = TX.gloss((226, 228, 222), sd("lampdome"), amp=1.2)
    M.grime(img, 0.1, seed=sd("lampdomeG"), color=(170, 160, 130), cells=(8, 4))
    TX.save(img, "lampdome")


# ======================================================================== Helpers

def ring_x(name, cx, cy, cz, r, t, x1, x2, tex, n=12, phase=0.0):
    """A ring (a tyre, a rim) in the y-z plane about (cy, cz), between x1 and x2: n tangent boxes each turned about x."""
    half = r * math.tan(math.pi / n) + 0.04
    els = []
    for k in range(n):
        els.append(B(f"{name}{k}", (x1, cy + r - t, cz - half), (x2, cy + r, cz + half), tex,
                     rot=(round(phase + k * 360.0 / n, 3), 0, 0), origin=(cx, cy, cz)))
    return els


def spokes_x(name, cx, cy, cz, r, x1, x2, tex, n=4, w=0.3, phase=0.0):
    return [B(f"{name}{k}", (x1, cy - w / 2, cz - r), (x2, cy + w / 2, cz + r), tex, rot=(round(phase + k * 180.0 / n, 3), 0, 0),
              origin=(cx, cy, cz)) for k in range(n)]


def halves(els, part):
    return clip_z(els, 16, 99, -16) if part == "head" else clip_z(els, -99, 16, 0)


# ======================================================================== Gurney

def gurney_model(kind):
    """A stretcher trolley 32 long (foot z 0-16, head z 16-32)."""
    T, D = "p-tubes", "p-darksteel"
    els = []
    for i, (x, z) in enumerate(((4.25, 3), (11.75, 3), (4.25, 29), (11.75, 29))):
        els += castor(f"Castor{i}", x, z, tex="p-ruststeel" if i == 2 else D)
    # the base frame: two tubes along the length and a cross tube at each end
    els += rod("BaseW", "z", 4.25, 2.75, 0.55, 2.25, 29.75, T)
    els += rod("BaseE", "z", 11.75, 2.75, 0.55, 2.25, 29.75, T)
    els += [B("BaseN", (4.75, 2.3, 2.6), (11.25, 3.2, 3.4), T, faces=no("east", "west")),
            B("BaseS", (4.75, 2.3, 28.6), (11.25, 3.2, 29.4), T, faces=no("east", "west")),
            B("Tray", (5, 3.4, 6), (11, 3.8, 26), "p-steel"),
            B("TrayLip", (5, 3.8, 6), (11, 4.3, 6.4), "p-steel", faces=no("down"))]
    # two hydraulic columns in their rubber bellows, a foot pedal at the head
    for i, z in enumerate((9, 23)):
        els += [B(f"ColFoot{i}", (6, 3.8, z - 2), (10, 4.6, z + 2), D),
                B(f"Bellows{i}", (6.6, 4.6, z - 1.4), (9.4, 7.8, z + 1.4), "p-bellows"),
                B(f"Ram{i}", (7.3, 7.8, z - 0.7), (8.7, 9.3, z + 0.7), "p-chrome", faces=no("down")),
                B(f"ColHead{i}", (6.25, 9.3, z - 1.75), (9.75, 9.8, z + 1.75), D)]
    els += [B("Pedal", (6.5, 2.4, 29.6), (9.5, 2.9, 31.6), D), B("PedalArm", (7.6, 2.4, 28.6), (8.4, 2.8, 29.6), D)]
    # the deck: a frame of tube round a perforated pan
    els += [B("DeckW", (3, 9.6, 1), (4, 10.5, 31), T), B("DeckE", (12, 9.6, 1), (13, 10.5, 31), T),
            B("DeckN", (4, 9.6, 1), (12, 10.5, 1.9), T, faces=no("east", "west")),
            B("DeckS", (4, 9.6, 30.1), (12, 10.5, 31), T, faces=no("east", "west")),
            B("Pan", (4, 9.8, 1.9), (12, 10.3, 30.1), "p-steel", faces=("down",))]
    # the mattress: the flat foot section, the back rest raised from z 21 (hinged), a pillow on it
    els += [B("Mattress", (3.4, 10.5, 1.3), (12.6, 12.4, 21), {"top": "p-mattress", "side": "p-mattress-side"})]
    back = [B("BackPan", (3.4, 10.4, 21), (12.6, 10.9, 30.2), "p-steel"),
            B("BackMat", (3.4, 10.9, 21.2), (12.6, 12.8, 30.4), {"top": "p-mattress", "side": "p-mattress-side"}),
            B("Pillow", (4.2, 12.8, 25.2), (11.8, 14.4, 30), "p-pillow")]
    els += turned(back, rx=-28, origin=(8, 10.5, 21))
    els += [B("Strut", (7.4, 10.4, 22.5), (8.6, 11, 26.5), D, rot=(-50, 0, 0), origin=(8, 10.7, 22.5))]
    sheet = "p-sheetstain" if kind == "strap" else "p-sheet"
    els += [B("Sheet", (3.2, 12.4, 2.5), (12.8, 12.75, 20.6), {"top": sheet, "side": sheet})]
    els += turned([B("SheetHang", (12.8, 6.8, 4), (13.25, 12.75, 15.6), sheet, faces=no("up"))], rz=-6, origin=(12.8, 12.75, 10))
    els += turned([B("SheetFold", (4, 12.75, 3), (12, 13.4, 7.5), sheet)], ry=7, origin=(8, 12.75, 5))
    # side rails: the west one up (two posts, two bars), the east one folded down beside the deck
    els += [B("RailWPostA", (2.55, 10.5, 6), (3.2, 14.6, 6.65), "p-chrome", faces=no("up", "down")),
            B("RailWPostB", (2.55, 10.5, 19.4), (3.2, 14.6, 20.05), "p-chrome", faces=no("up", "down")),
            B("RailWTop", (2.45, 14.6, 5.4), (3.3, 15.4, 20.6), T),
            B("RailWMid", (2.6, 12.6, 6.65), (3.15, 13.1, 19.4), "p-chrome"),
            B("RailEBar", (13.05, 7.4, 5.4), (13.9, 8.2, 20.6), T),
            B("RailEMid", (13.2, 8.9, 6.65), (13.75, 9.4, 19.4), "p-chrome"),
            B("RailEHingeA", (12.9, 8.2, 6), (13.6, 9.6, 6.65), D), B("RailEHingeB", (12.9, 8.2, 19.4), (13.6, 9.6, 20.05), D)]
    # the push bar at the head end, an IV socket at a corner
    els += [B("PushW", (3.4, 10.5, 31), (4.2, 16.4, 31.8), T, faces=no("down")),
            B("PushE", (11.8, 10.5, 31), (12.6, 16.4, 31.8), T, faces=no("down")),
            B("PushBar", (3.4, 16.4, 30.9), (12.6, 17.3, 31.9), {"all": "p-rubber"}),
            B("IvSocket", (12.3, 10.5, 1.2), (13.2, 12.2, 2.1), D)]
    if kind == "strap":
        for i, z in enumerate((4.5, 11, 17.5)):
            els += [B(f"Strap{i}", (3.1, 12.75, z), (12.9, 13.15, z + 1.6), "p-leather", faces=no("down")),
                    B(f"StrapW{i}", (2.95, 9.5, z), (3.4, 13.15, z + 1.6), "p-leather", faces=no("up")),
                    B(f"StrapE{i}", (12.6, 9.5, z), (13.05, 13.15, z + 1.6), "p-leather", faces=no("up")),
                    B(f"Buckle{i}", (9, 13.15, z - 0.15), (10.4, 13.45, z + 1.75), "p-chrome", faces=no("down"))]
        els.append(pic(B("Stain", (5, 12.77, 9), (11.5, 12.8, 16), "p-blood", faces=("up",)), "up", "p-bloodpool"))
        els += [B("Drip", (12.9, 4, 12), (13.2, 9.5, 12.4), "p-blood", faces=("east", "north", "south"))]
    return els


def gurney(part, kind):
    return halves(gurney_model(kind), part)


# ======================================================================== Wheelchair

def wheelchair():
    """A hospital wheelchair facing north: the big wheels at the back (tyres, rims, spokes, push rims), front castors,
    a folding X brace, a black vinyl sling seat and back, arm pads, footplates (the east one folded up), handles."""
    T, D, V = "p-tubes", "p-darksteel", "p-sling"
    cy, cz, r = 5.6, 11.2, 5.5
    els = []
    for s, (x1, x2, px1, px2, sx) in (("W", (0.9, 1.9, 0.15, 0.55, 1.4)), ("E", (14.1, 15.1, 15.45, 15.85, 14.6))):
        els += ring_x(f"Tyre{s}", sx, cy, cz, r, 0.9, x1, x2, "p-rubber", n=14)
        els += ring_x(f"Rim{s}", sx, cy, cz, r - 0.9, 0.4, x1 + 0.2, x2 - 0.2, "p-chrome", n=14, phase=6)
        els += ring_x(f"Push{s}", sx, cy, cz, r - 0.6, 0.35, px1, px2, "p-chrome", n=12, phase=12)
        els += spokes_x(f"Spoke{s}", sx, cy, cz, r - 1.1, sx - 0.12, sx + 0.12, "p-chrome", n=6, w=0.22, phase=8)
        els += rod(f"Hub{s}", "x", cy, cz, 0.7, x1 - 0.1, x2 + 0.1, D)
    # the side frames (west at x 2.4-3.1, east 12.9-13.6)
    for s, x in (("W", 2.4), ("E", 12.9)):
        X = (x, x + 0.7)
        els += [B(f"Low{s}", (X[0], 3.1, 2.4), (X[1], 3.8, 12.8), T),
                B(f"SeatRail{s}", (X[0], 7.5, 2.4), (X[1], 8.2, 12.4), T),
                B(f"Front{s}", (X[0], 3.8, 2.4), (X[1], 7.5, 3.1), T, faces=no("up", "down")),
                B(f"AxlePlate{s}", (X[0] - 0.05, 4.2, 10), (X[1] + 0.05, 7, 12.4), D),
                B(f"ArmPostA{s}", (X[0] + 0.1, 8.2, 4.8), (X[1] - 0.1, 11.2, 5.4), D, faces=no("up", "down")),
                B(f"ArmPostB{s}", (X[0] + 0.1, 8.2, 10.6), (X[1] - 0.1, 11.2, 11.2), D, faces=no("up", "down")),
                B(f"ArmPad{s}", (X[0] - 0.3, 11.2, 4.2), (X[1] + 0.3, 12.1, 11.8), V),
                B(f"Hanger{s}", (X[0], 0.9, 1.6), (X[1], 4.0, 2.3), T, rot=(-24, 0, 0), origin=(x + 0.35, 3.8, 2.6))]
        back = [B(f"Upright{s}", (X[0], 3.8, 12.4), (X[1], 15.4, 13.1), T, faces=no("down")),
                B(f"Grip{s}", (X[0] - 0.1, 15.0, 13.1), (X[1] + 0.1, 15.8, 16), "p-rubber")]
        els += turned(back, rx=6, origin=(x + 0.35, 3.8, 12.75))
        els += castor(f"Castor{s}", x + 0.35, 2.1, y=0.3)
        els += [B(f"Stem{s}", (x + 0.05, 2.55, 1.8), (x + 0.65, 3.1, 2.4), D)]
    els += turned([B("BackSling", (3.1, 8.6, 12.45), (12.9, 15.0, 12.95), V),
                   B("BackPocket", (4.2, 9.2, 12.95), (11.8, 12.2, 13.3), V)], rx=6, origin=(8, 3.8, 12.75))
    els += [B("Seat", (3.1, 7.6, 2.6), (12.9, 8.1, 12.3), V),
            B("SeatSag", (3.6, 7.25, 3.4), (12.4, 7.6, 11.4), V, faces=("down",))]
    for k, a in enumerate((21, -21)):
        els.append(B(f"Brace{k}", (3.3, 5.4, 7.6), (12.7, 5.9, 8.2), T, rot=(0, 0, a), origin=(8, 5.65, 7.9)))
    # footplates: the west down, the east folded up against its hanger
    els += [B("FootW", (2.6, 0.75, 0.0), (7.6, 1.15, 2.4), "p-darksteel"),
            B("FootE", (12.6, 1.0, 0.0), (13.0, 5.6, 2.4), "p-darksteel")]
    els += [B("Rust", (2.35, 3.05, 6), (3.15, 3.85, 8), "p-ruststeel")]
    return els


# ======================================================================== Drip stand

def ivstand():
    """A drip stand: a five-castor base, a pole two blocks high with a four-hook crown, a saline bag and its giving set
    running to an infusion pump clamped on the pole (its panel to the north), the line looping on below."""
    els = five_star("Base", tex="p-ruststeel")
    els += rod("Pole", "y", 8, 8, 0.45, 2.0, 29.2, "p-chrome")
    els += [B("Collar", (7.3, 14.2, 7.3), (8.7, 14.9, 8.7), "p-darksteel"),
            B("Knob", (8.7, 14.35, 7.8), (9.6, 14.75, 8.2), "p-darkplastic"),
            B("Crown", (7.3, 28.5, 7.3), (8.7, 29.6, 8.7), "p-chrome")]
    for k, (dx, dz) in enumerate(((0, -1), (1, 0), (0, 1), (-1, 0))):
        x1, x2 = sorted((8 + dx * 0.6, 8 + dx * 3.2)) if dx else (7.75, 8.25)
        z1, z2 = sorted((8 + dz * 0.6, 8 + dz * 3.2)) if dz else (7.75, 8.25)
        els += [B(f"HookArm{k}", (x1, 29.0, z1), (x2, 29.5, z2), "p-chrome")]
        hx, hz = 8 + dx * 3.0, 8 + dz * 3.0
        els += [B(f"HookUp{k}", (hx - 0.25, 29.5, hz - 0.25), (hx + 0.25, 30.4, hz + 0.25), "p-chrome", faces=no("down"))]
    # the bag on the north hook, its drip chamber and the line down to the pump
    bag = transparent(B("Bag", (6.4, 22.2, 4.4), (9.6, 27.6, 5.6), "p-saline"))
    els += [bag, B("BagTop", (7.4, 27.6, 4.75), (8.6, 29.2, 5.25), "p-tube"),
            B("Port", (7.7, 21.4, 4.8), (8.3, 22.2, 5.2), "p-tube"),
            B("Chamber", (7.55, 19.8, 4.75), (8.45, 21.4, 5.25), "p-tube"),
            B("LineA", (7.9, 17.6, 4.9), (8.1, 19.8, 5.1), "p-tube")]
    # the pump, clamped to the pole
    els += [B("Pump", (5.4, 13.0, 4.6), (10.6, 17.6, 7.4), {"all": "p-greyplastic", "front": "p-greyplastic"}),
            pic(B("PumpFace", (5.6, 13.2, 4.45), (10.4, 17.4, 4.6), "p-greyplastic", faces=("north",)), "north", "p-pump"),
            B("Clamp", (7.0, 14.6, 7.4), (9.0, 16.0, 8.9), "p-darksteel"),
            B("ClampScrew", (9.0, 15.0, 7.9), (10.6, 15.6, 8.5), "p-chrome"),
            B("Handle", (6.4, 17.6, 5.6), (9.6, 18.2, 6.4), "p-darkplastic"),
            B("LineB", (7.9, 4.0, 4.4), (8.1, 13.0, 4.6), "p-tube"),
            B("LineLoop", (8.1, 4.0, 4.4), (12.5, 4.2, 4.6), "p-tube"),
            B("LineEnd", (12.3, 0.1, 4.4), (12.5, 4.2, 4.6), "p-tube"),
            B("LineFloor", (12.3, 0.05, 1.5), (12.5, 0.25, 4.6), "p-tube")]
    return els


# ======================================================================== Surgical light

def lamp_head(name, cx, cy, cz, r=3.2):
    """A surgical lamp head, its lens facing down, the lens's plane at cy: a dome of octagonal tiers (a smooth
    shoulder), a chrome rim, a lit lens with its reflector rings, a sterile handle in the middle."""
    els = []
    for k, (rr, y1, y2) in enumerate(((r, 0, 0.7), (r * 0.94, 0.7, 1.3), (r * 0.82, 1.3, 1.9), (r * 0.64, 1.9, 2.4),
                                      (r * 0.4, 2.4, 2.8), (r * 0.2, 2.8, 3.6))):
        els += octagon(f"{name}Dome{k}", cx, cz, rr, cy + y1, cy + y2, "p-lampdome" if k < 5 else "p-chrome", step=0.01)
    els += octagon(f"{name}Rim", cx, cz, r + 0.2, cy - 0.3, cy + 0.15, "p-chrome", faces=no("up"), step=0.01)
    for k, rr in enumerate((r * 0.92, r * 0.55)):
        els += [pic(e, "down", "p-lens", glow=255) for e in
                octagon(f"{name}Lens{k}", cx, cz, rr, cy - 0.38 - k * 0.04, cy - 0.3, "p-lamphead", faces=("down",), step=0.002)]
    els += [B(f"{name}Grip", (cx - 0.45, cy - 2.2, cz - 0.45), (cx + 0.45, cy - 0.4, cz + 0.45), "p-greyplastic", faces=no("up")),
            B(f"{name}GripCap", (cx - 0.65, cy - 2.5, cz - 0.65), (cx + 0.65, cy - 2.2, cz + 0.65), "p-greyplastic")]
    return els


def surglamp():
    """A surgical light in the top block of a room: a ceiling canopy, the drop tube, a hub, two arms out (one north,
    one east and lower) with spring housings, each ending in a yoke that holds a lamp head over the table below."""
    W = "p-lampdome"
    els = octagon("Canopy", 8, 8, 3.0, 15.3, 16, W)
    els += rod("Drop", "y", 8, 8, 0.75, 11.6, 15.3, "p-chrome")
    els += rod("Hub", "y", 8, 8, 1.3, 10.4, 11.9, W)
    # arm 1, north: a straight arm with its spring housing, an elbow, a stem down to the yoke
    els += [B("ArmN", (7.45, 10.7, 3.2), (8.55, 11.6, 8), W),
            B("SpringN", (7.25, 10.55, 5.4), (8.75, 11.75, 7.2), "p-darksteel"),
            B("ElbowN", (7.1, 10.1, 2.4), (8.9, 11.8, 4.0), W)]
    els += rod("StemN", "y", 8, 3.2, 0.45, 9.0, 10.1, "p-chrome")
    # arm 2, east and a little lower
    els += [B("ArmE", (8, 9.4, 7.45), (13.6, 10.3, 8.55), W),
            B("SpringE", (9.4, 9.25, 7.25), (11.4, 10.45, 8.75), "p-darksteel"),
            B("ElbowE", (12.8, 8.8, 7.1), (14.4, 10.5, 8.9), W)]
    els += rod("StemE", "y", 13.6, 8, 0.45, 7.6, 8.8, "p-chrome")
    # the yokes (a bar across, two legs down to the head's pivots) and the heads
    for s, (cx, cz, ytop, along_x) in (("N", (8, 3.2, 9.0, True)), ("E", (13.6, 8, 7.6, False))):
        r = 2.9
        if along_x:
            els += [B(f"Yoke{s}", (cx - r - 0.8, ytop - 0.6, cz - 0.35), (cx + r + 0.8, ytop, cz + 0.35), W),
                    B(f"YokeA{s}", (cx - r - 0.8, ytop - 3.6, cz - 0.35), (cx - r - 0.2, ytop - 0.6, cz + 0.35), W, faces=no("up")),
                    B(f"YokeB{s}", (cx + r + 0.2, ytop - 3.6, cz - 0.35), (cx + r + 0.8, ytop - 0.6, cz + 0.35), W, faces=no("up"))]
        else:
            els += [B(f"Yoke{s}", (cx - 0.35, ytop - 0.6, cz - r - 0.8), (cx + 0.35, ytop, cz + r + 0.8), W),
                    B(f"YokeA{s}", (cx - 0.35, ytop - 3.6, cz - r - 0.8), (cx + 0.35, ytop - 0.6, cz - r - 0.2), W, faces=no("up")),
                    B(f"YokeB{s}", (cx - 0.35, ytop - 3.6, cz + r + 0.2), (cx + 0.35, ytop - 0.6, cz + r + 0.8), W, faces=no("up"))]
        els += lamp_head(f"Head{s}", cx, ytop - 5.0, cz, r=r)
    return els


# ======================================================================== Operating table

def optable_model():
    """An operating table 32 long (foot z 0-16, head z 16-32) on one column at the middle (across the joint): a base
    plate, the column with its shroud and control box, the top tilted head-down about the column's head (each half
    turned about the same point so the top stays one), pads, side rails, a headrest, arm boards out to both sides,
    restraint straps, a stained drape slid half off."""
    S_ = "p-steel"
    els = [B("Base", (3.5, 0, 9), (12.5, 1.2, 23), {"top": "p-whiteworn", "side": "p-whiteworn"}),
           B("BasePlinth", (4, 0, 8.5), (12, 0.6, 23.5), "p-darksteel", faces=no("up", "down")),
           B("Foot0", (3.2, 0, 9.2), (5, 0.6, 11), "p-rubber"), B("Foot1", (11, 0, 9.2), (12.8, 0.6, 11), "p-rubber"),
           B("Foot2", (3.2, 0, 21), (5, 0.6, 22.8), "p-rubber"), B("Foot3", (11, 0, 21), (12.8, 0.6, 22.8), "p-rubber")]
    els += rod("Shroud", "y", 8, 16, 2.6, 1.2, 6.5, "p-whiteworn")
    els += rod("Column", "y", 8, 16, 1.9, 6.5, 10.4, "p-chrome")
    els += [B("Control", (10.2, 3, 14.5), (12.2, 6, 17.5), {"all": "p-greyplastic"}),
            B("ColHead", (5.5, 10.4, 13.5), (10.5, 11.2, 18.5), "p-darksteel")]
    top = []
    for part, z1, z2 in (("F", 1.5, 16), ("H", 16, 28.5)):
        top += [B(f"Frame{part}", (3, 11.2, z1), (13, 12.1, z2), S_),
                B(f"Pad{part}", (3.2, 12.1, z1 + 0.2), (12.8, 13.7, z2 - 0.2), "p-optpad"),
                B(f"RailW{part}", (2.2, 11.3, z1 + 0.6), (2.75, 12.0, z2 - 0.6), "p-chrome"),
                B(f"RailE{part}", (13.25, 11.3, z1 + 0.6), (13.8, 12.0, z2 - 0.6), "p-chrome")]
    foot, head = [], []
    head += [B("HeadFrame", (5, 11.2, 28.5), (11, 12.1, 31.6), S_),
             B("HeadPad", (5.2, 12.1, 28.6), (10.8, 13.6, 31.4), "p-optpad"),
             B("ArmBoardW", (-3.5, 11.6, 21.5), (3, 12.4, 24.5), S_), B("ArmPadW", (-3.3, 12.4, 21.7), (2.8, 13.4, 24.3), "p-optpad"),
             B("ArmBoardE", (13, 11.6, 21.5), (19.5, 12.4, 24.5), S_), B("ArmPadE", (13.2, 12.4, 21.7), (19.3, 13.4, 24.3), "p-optpad"),
             B("CuffW", (-2.2, 13.4, 22.3), (-0.6, 13.8, 23.7), "p-leather"), B("CuffE", (16.6, 13.4, 22.3), (18.2, 13.8, 23.7), "p-leather"),
             B("StrapH", (3, 13.7, 18.5), (13, 14.05, 20.2), "p-leather"),
             B("BuckleH", (9, 14.05, 18.35), (10.4, 14.3, 20.35), "p-chrome")]
    foot += [B("StrapF", (3, 13.7, 5), (13, 14.05, 6.7), "p-leather"),
             B("Drape", (3.6, 13.7, 8.5), (13.4, 14.0, 15.5), "p-drapestain"),
             B("DrapeHang", (13.4, 7.0, 8.5), (13.7, 14.0, 15.5), "p-drapestain")]
    for e in top:
        (foot if e["name"].endswith("F") else head).append(e)
    pivot = dict(rx=-9, origin=(8, 11.2, 16))
    return els + turned(foot, **pivot) + turned(head, **pivot)


def optable(part):
    return halves(optable_model(), part)


# ======================================================================== Stretchers (torture chambers)

def stretcher(name, y, x=8, z=8, ry=0, rz=0, torn=False):
    """A rusted steel field stretcher lying along z centred on (x, z), its feet on y: two tubular poles with handles
    beyond the ends, the stirrup legs, the spreader bars, the stained pad (split when torn)."""
    T = "p-tubes" if not torn else "p-ruststeel"
    els = rod(name + "PoleW", "z", x - 4.1, y + 1.6, 0.45, z - 8.6, z + 8.6, T)
    els += rod(name + "PoleE", "z", x + 4.1, y + 1.6, 0.45, z - 8.6, z + 8.6, T)
    els += [B(name + "GripWN", (x - 4.6, y + 1.1, z - 8.6), (x - 3.6, y + 2.1, z - 7.2), "p-rubber"),
            B(name + "GripES", (x + 3.6, y + 1.1, z + 7.2), (x + 4.6, y + 2.1, z + 8.6), "p-rubber")]
    for k, zz in enumerate((z - 5.4, z + 5.4)):
        els += [B(f"{name}Bar{k}", (x - 3.7, y + 1.3, zz - 0.3), (x + 3.7, y + 1.8, zz + 0.3), "p-ruststeel"),
                B(f"{name}LegW{k}", (x - 4.3, y, zz - 0.3), (x - 3.8, y + 1.3, zz + 0.3), "p-ruststeel", faces=no("up")),
                B(f"{name}LegE{k}", (x + 3.8, y, zz - 0.3), (x + 4.3, y + 1.3, zz + 0.3), "p-ruststeel", faces=no("up")),
                B(f"{name}Stir{k}", (x - 4.3, y, zz - 0.3), (x + 4.3, y + 0.4, zz + 0.3), "p-ruststeel", faces=no("east", "west"))]
    pad = {"top": "p-stretchpad", "side": "p-stretchpad", "bottom": "p-ruststeel"}
    if torn:
        els += [B(name + "PadA", (x - 3.65, y + 1.5, z - 7.4), (x + 3.65, y + 1.95, z - 0.8), pad),
                B(name + "PadB", (x - 3.65, y + 1.5, z + 1.4), (x + 3.65, y + 1.95, z + 7.4), pad)]
        els += [B(name + "Flap", (x - 3.2, y + 0.2, z - 0.8), (x + 1, y + 1.95, z - 0.4), "p-stretchpad", faces=no("up"))]
    else:
        els += [B(name + "Pad", (x - 3.65, y + 1.5, z - 7.4), (x + 3.65, y + 1.95, z + 7.4), pad)]
    return turned(els, ry=ry, rz=rz, origin=(x, y, z))


def stretchers(part):
    """Rusted stretchers stacked atop each other, askew, a block and a half high (lower, upper)."""
    els = []
    if part == "lower":
        for i, (y, x, z, ry, rz) in enumerate(((0, 8, 8, 0, 0), (2.5, 7.4, 8.4, 8, 2), (5.0, 8.6, 7.5, -6, -3),
                                                 (7.5, 7.7, 8.3, 12, 1), (10.0, 8.6, 8.4, -4, 3), (12.5, 7.5, 7.7, 9, -2))):
            els += stretcher(f"S{i}", y, x, z, ry, rz, torn=i in (1, 4))
        els += [B("BloodDrip", (3.5, 3.0, 2.0), (3.75, 9.5, 2.4), "p-blood", faces=("west", "north", "east"))]
    else:
        for i, (y, x, z, ry, rz) in enumerate(((-1.0, 8.3, 8.2, -8, 1), (1.5, 7.6, 7.8, 4, -3), (4.0, 8.5, 8.5, -12, 2))):
            els += stretcher(f"S{i}", y, x, z, ry, rz, torn=i == 1)
        els += stretcher("Slid", 6.8, 9, 7.2, 24, -9, torn=True)
    return els


# ======================================================================== The nurses' station's back unit

def stationback(part, kind):
    """The back wall unit behind a nurses' station counter, two blocks high, its front to the north, its back flush
    with the block's south edge (it stands against a wall): lower, a laminate cupboard with a worktop and pigeonholes
    over it; upper, a whiteboard of names in an aluminium frame with a marker tray (board) or a rack of patient chart
    binders (files), and a cornice with a strip light."""
    L = {"front": "p-laminate", "side": "p-whiteworn", "back": "p-whiteworn", "top": "p-whiteworn", "bottom": "p-whiteworn"}
    els = []
    if part == "lower":
        els += [B("Plinth", (0.3, 0, 7.4), (15.7, 1.2, 15), "p-teal"),
                B("Carcass", (0, 1.2, 7), (16, 8.8, 16), L),
                B("Top", (0, 8.8, 6.2), (16, 9.6, 16), {"top": "p-worktop", "side": "p-teal", "bottom": "p-teal"})]
        for i, x in enumerate((0.4, 8.2)):
            els += [B(f"Door{i}", (x, 1.6, 6.7), (x + 7.4, 8.4, 7), "p-laminate", faces=no("south")),
                    B(f"Pull{i}", (x + (6.2 if i == 0 else 0.6), 6.2, 6.1), (x + (6.8 if i == 0 else 1.2), 8.0, 6.7), "p-chrome")]
        els += [B("Shelf", (0, 12.2, 9.5), (16, 12.7, 16), "p-whiteworn"),
                B("SideW", (0, 9.6, 9.5), (0.6, 16, 16), "p-whiteworn"), B("SideE", (15.4, 9.6, 9.5), (16, 16, 16), "p-whiteworn"),
                pic(B("Holes", (0.6, 12.7, 10.5), (15.4, 16, 15.9), "p-darkplastic", faces=("north",)), "north", "p-pigeonholes"),
                B("Back", (0.6, 9.6, 15.5), (15.4, 16, 16), "p-whiteworn", faces=("north",)),
                B("Phone", (2, 9.6, 10), (5.5, 10.8, 13), "p-beige"), B("Handset", (2.2, 10.8, 10.3), (5.3, 11.5, 11.3), "p-beige-side"),
                pic(B("Papers", (7, 9.6, 8), (12, 9.7, 12), "p-papers", faces=("up",)), "up", "p-chart"),
                B("Mug", (13, 9.6, 9.5), (14.2, 11.0, 10.7), "p-white")]
        els += turned([B("Binder", (9, 9.6, 12.5), (13, 10.4, 15), {"all": "p-liqblue", "top": "p-folder"})], ry=8, origin=(11, 9.6, 13.7))
    else:
        els += [B("Panel", (0, 0, 15), (16, 15.2, 16), "p-whiteworn", faces=("north", "up", "east", "west"))]
        if kind == "board":
            els += [B("FrameT", (0.6, 12.6, 14.2), (15.4, 13.2, 15), "p-chrome"), B("FrameB", (0.6, 2.4, 14.2), (15.4, 3.0, 15), "p-chrome"),
                    B("FrameW", (0.6, 3.0, 14.2), (1.2, 12.6, 15), "p-chrome"), B("FrameE", (14.8, 3.0, 14.2), (15.4, 12.6, 15), "p-chrome"),
                    pic(B("Board", (1.2, 3.0, 14.6), (14.8, 12.6, 15), "p-white", faces=("north",)), "north", "p-namesboard"),
                    B("Tray", (1.5, 2.1, 13.2), (14.5, 2.5, 15), "p-chrome"),
                    B("TrayLip", (1.5, 2.5, 13.2), (14.5, 2.9, 13.5), "p-chrome", faces=no("down")),
                    B("MarkerA", (3, 2.5, 13.6), (5.6, 2.95, 14.1), "p-liqblue"), B("MarkerB", (6.2, 2.5, 13.7), (8.8, 2.95, 14.2), "p-liqred"),
                    B("Eraser", (10.5, 2.5, 13.5), (12.8, 3.4, 14.5), "p-darkplastic")]
        else:
            els += [B("RackBack", (0.6, 1.2, 12.5), (15.4, 11.6, 15), "p-darksteel", faces=("north", "up", "down")),
                    pic(B("Spines", (1.0, 1.6, 12.3), (15.0, 11.2, 12.5), "p-black", faces=("north",)), "north", "p-binders"),
                    B("RackW", (0.4, 1.0, 11.6), (1.0, 11.8, 15), "p-darksteel"), B("RackE", (15.0, 1.0, 11.6), (15.6, 11.8, 15), "p-darksteel"),
                    B("RackShelf", (0.4, 6.2, 11.6), (15.6, 6.6, 15), "p-darksteel"),
                    B("RackBase", (0.4, 1.0, 11.6), (15.6, 1.6, 15), "p-darksteel")]
            els += turned([B("Leaning", (11, 6.6, 12.6), (12.6, 11.4, 14.8), {"all": "p-liqred", "front": "p-liqred"})], rz=-14, origin=(12.6, 6.6, 13.7))
        els += [B("Cornice", (0, 15.2, 13), (16, 16, 16), "p-whiteworn"),
                B("Strip", (1, 14.8, 13.4), (15, 15.2, 14.6), "p-white", glow=0)]
    return [e for e in els if e is not None]


# ======================================================================== Wall decorations as models (tools/gen_14.py)

DECO_WALLS = ["paint", "white", "tile", "tileblood", "rust", "mould", "cinder", "concrete", "plywood", "padded"]
DECALS = ("blood", "blooddrip", "mould", "scratches", "trg")


def deco_cutouts(G):
    """Turns every deco-* picture (drawn by gen_14.deco_textures on the mint wall) into a cut-out: it draws them a second
    time on the inverted wall, and where a pixel differs it works out how much of the wall showed through and the colour
    drawn over it; a pixel more than half the decoration's own is kept (alpha 255), the rest is cut away (alpha 0).
    Returns {name: bbox in px (x0, y0, x1, y1) of what is kept}."""
    from PIL import ImageOps
    orig_save, orig_base = G.save, G.deco_base
    alt = {}

    def cap(img, name):
        if name.startswith("deco-"):
            alt[name] = img.copy()
        else:
            orig_save(img, name)

    G.save = cap
    G.deco_base = lambda: ImageOps.invert(orig_base().convert("RGB")).convert("RGBA")
    try:
        G.deco_textures()
    finally:
        G.save, G.deco_base = orig_save, orig_base
    base_a = orig_base()
    base_b = ImageOps.invert(base_a.convert("RGB")).convert("RGBA")
    bboxes = {}
    for name, b in alt.items():
        a = G.load(name)
        w, h = a.size
        pa, pb, ba, bb = a.load(), b.load(), base_a.load(), base_b.load()
        out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        po = out.load()
        for y in range(h):
            for x in range(w):
                ca, cb = pa[x, y], pb[x, y]
                wa, wb = ba[x % base_a.width, y % base_a.height], bb[x % base_a.width, y % base_a.height]
                k = max(range(3), key=lambda i: abs(wa[i] - wb[i]))
                span = wa[k] - wb[k]
                t = 1.0 - (ca[k] - cb[k]) / span if span else 1.0
                if t >= 0.5:
                    t = min(1.0, t)
                    c = tuple(M.clamp((ca[i] - (1 - t) * wa[i]) / t) for i in range(3))
                    po[x, y] = c + (255,)
        orig_save(out, name)
        bboxes[name] = out.getbbox() or (0, 0, w, h)
    return bboxes


def _face(name, bbox, z1, z2, key, side_tex, glow_=0, faces=None):
    """An element over a picture's kept area (bbox in 64-px texels), from z1 to z2 (negative: proud of the wall's north
    face), its north face showing that part of the picture."""
    x0, y0, x1, y1 = bbox
    u0, v0, u1, v1 = x0 / 4, y0 / 4, x1 / 4, y1 / 4
    el = B(name, (16 - u1, 16 - v1, z1), (16 - u0, 16 - v0, z2), side_tex, faces=faces or no("south"))
    pic(el, "north", key, glow=glow_, uv=(round(u0, 4), round(v0, 4), round(u1, 4), round(v1, 4)))
    return el


def deco_model(kind, bbox):
    """The elements of one wall decoration (north face dressed): the wall cube (texture key "wall", set by the block
    type to the wall's own material) and the decoration on it."""
    key = "deco-" + kind
    els = [B("Wall", (0, 0, 0), (16, 16, 16), "wall")]
    x0, y0, x1, y1 = [v / 4 for v in bbox]
    xa, xb, ya, yb = 16 - x1, 16 - x0, 16 - y1, 16 - y0
    if kind.startswith("plate-"):
        els.append(_face("Plate", bbox, -0.35, 0, key, "p-darkplastic"))
    elif kind.startswith("directory-"):
        els.append(_face("Board", bbox, -0.7, 0, key, "p-chrome"))
    elif kind.startswith("sign-"):
        els.append(_face("Sign", bbox, -0.6, 0, key, "p-darksteel"))
        ym = (ya + yb) / 2
        for i, x in enumerate((xa + 1.2, xb - 1.2)):
            els.append(B(f"Screw{i}", (x - 0.25, ym - 0.25, -0.75), (x + 0.25, ym + 0.25, -0.6), "p-chrome"))
    elif kind.startswith("poster-"):
        els.append(_face("Poster", bbox, -0.08, 0, key, "p-papers"))
    elif kind in DECALS:
        els.append(_face("Decal", bbox, -0.06, 0, key, "p-papers", faces=("north",)))
    elif kind == "clock":
        els += clock_model(bbox, key)
    elif kind == "whiteboard":
        els.append(_face("Board", bbox, -0.45, 0, key, "p-chrome"))
        els += [B("Tray", (xa + 0.5, ya - 0.6, -1.6), (xb - 0.5, ya, -0.2), "p-chrome"),
                B("TrayLip", (xa + 0.5, ya, -1.6), (xb - 0.5, ya + 0.35, -1.3), "p-chrome", faces=no("down")),
                B("MarkerA", (xa + 1.5, ya, -1.2), (xa + 4.0, ya + 0.45, -0.75), "p-liqblue"),
                B("MarkerB", (xa + 4.6, ya, -1.25), (xa + 7.0, ya + 0.45, -0.8), "p-liqred"),
                B("Eraser", (xb - 4.5, ya, -1.3), (xb - 2.2, ya + 0.9, -0.5), "p-darkplastic")]
    elif kind == "xray":
        els += [B("Box", (xa - 0.5, ya - 0.5, -1.4), (xb + 0.5, yb + 0.5, 0), "p-steel"),
                _face("Screen", bbox, -1.5, -1.4, key, "p-steel", glow_=150, faces=("north",)),
                B("Clip0", (xa + 1.5, yb - 0.3, -1.8), (xa + 2.7, yb + 0.6, -1.4), "p-chrome"),
                B("Clip1", (xb - 2.7, yb - 0.3, -1.8), (xb - 1.5, yb + 0.6, -1.4), "p-chrome"),
                B("Switch", (xb - 1.2, ya - 0.4, -1.7), (xb - 0.4, ya + 0.4, -1.4), "p-darkplastic")]
    elif kind == "exitsign":
        els += [B("Housing", (xa - 0.4, ya - 0.4, -2.2), (xb + 0.4, yb + 0.4, 0), "p-white"),
                _face("Panel", bbox, -2.3, -2.2, key, "p-white", glow_=170, faces=("north",)),
                B("Lip", (xa - 0.6, yb + 0.4, -2.5), (xb + 0.6, yb + 0.8, 0), "p-white"),
                B("Led", (xb - 1.0, ya - 0.35, -2.35), (xb - 0.5, ya - 0.05, -2.2), "p-liqred", glow=200)]
    elif kind == "sanitizer":
        els += sanitizer_model()
    elif kind == "extinguisher":
        els += extinguisher_model()
    return els


def clock_model(bbox, key):
    """A wall clock: a dark bezel ring (an octagon of crossed boxes), the dial behind its glass, the hands stopped."""
    x0, y0, x1, y1 = [v / 4 for v in bbox]
    cx, cy = 16 - (x0 + x1) / 2, 16 - (y0 + y1) / 2
    r = max(x1 - x0, y1 - y0) / 2
    a = r * math.tan(math.pi / 8)
    els = []
    for k, (hx, hy, rz) in enumerate(((r + 0.4, a + 0.2, 0), (a + 0.2, r + 0.4, 0), (r + 0.4, a + 0.2, 45), (a + 0.2, r + 0.4, 45))):
        els.append(B(f"Bezel{k}", (cx - hx, cy - hy, -1.3 + k * 0.01), (cx + hx, cy + hy, 0), "p-darkplastic",
                     rot=(0, 0, rz) if rz else None, origin=(cx, cy, -0.65)))
    # the dial: the picture over two crossed boxes (not turned, so their UVs are the picture's own)
    for k, (hx, hy) in enumerate(((r - 0.1, a), (a, r - 0.1))):
        fx0, fx1, fy0, fy1 = cx - hx, cx + hx, cy - hy, cy + hy
        el = B(f"Dial{k}", (fx0, fy0, -1.36 - k * 0.01), (fx1, fy1, -1.3), "p-white", faces=("north",))
        pic(el, "north", key, uv=(round(16 - fx1, 4), round(16 - fy1, 4), round(16 - fx0, 4), round(16 - fy0, 4)))
        els.append(el)
    els += [B("HandH", (cx - 0.2, cy - 0.2, -1.7), (cx + 0.2, cy + r * 0.5, -1.55), "p-black", rot=(0, 0, -62), origin=(cx, cy, -1.6)),
            B("HandM", (cx - 0.15, cy - 0.3, -1.85), (cx + 0.15, cy + r * 0.78, -1.72), "p-black", rot=(0, 0, 140), origin=(cx, cy, -1.8)),
            B("Pin", (cx - 0.3, cy - 0.3, -1.95), (cx + 0.3, cy + 0.3, -1.4), "p-liqred")]
    return els


def sanitizer_model():
    """A wall-mounted hand gel dispenser: a white body with a window on the gel, the push lever, the nozzle, a drip tray
    stained under it, a sticker."""
    x1, x2, y1, y2 = 5.6, 10.4, 7.5, 13.2
    return [B("Back", (x1 - 0.3, y1 - 0.3, -0.4), (x2 + 0.3, y2 + 0.3, 0), "p-greyplastic"),
            B("Body", (x1, y1, -2.6), (x2, y2, -0.4), "p-white"),
            B("Top", (x1 + 0.2, y2, -2.4), (x2 - 0.2, y2 + 0.4, -0.4), "p-white"),
            B("Window", (x1 + 1.2, y1 + 2.2, -2.7), (x2 - 1.2, y2 - 1.2, -2.6), "p-liqblue", faces=("north",)),
            B("Lever", (x1 + 0.6, y1 - 0.2, -3.2), (x2 - 0.6, y1 + 1.6, -2.6), "p-greyplastic"),
            B("Nozzle", (7.6, y1 - 0.9, -1.9), (8.4, y1, -1.1), "p-darkplastic"),
            B("Tray", (6.2, 3.6, -2.4), (9.8, 4.1, -0.2), "p-greyplastic"),
            B("TrayStain", (6.6, 4.1, -2.0), (9.4, 4.15, -0.6), "p-liqamber", faces=("up",)),
            B("TrayArm", (7.6, 4.1, -0.6), (8.4, 7.2, -0.2), "p-greyplastic"),
            B("Sticker", (x1 + 1.0, y2 - 1.0, -2.65), (x2 - 1.0, y2 - 0.4, -2.6), "p-liqred", faces=("north",))]


def _ext_source():
    import json
    import os
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "backrooms", "shapes", "block", "detail",
                       "concretedeco-extinguisher.json")
    return json.load(open(src, encoding="utf-8"))


def extinguisher_model():
    """The mod's own wall extinguisher (shapes/block/detail/concretedeco-extinguisher.json, Level 1): its geometry and
    textures (keys prefixed ext-), less its wall."""
    import json
    out = []
    for e in _ext_source()["elements"]:
        if e["name"] == "Wall":
            continue
        e = json.loads(json.dumps(e))
        for f in e["faces"].values():
            f["texture"] = "#ext-" + f["texture"][1:]
        out.append(e)
    return out


def ext_textures():
    """The shared extinguisher's texture paths, by the keys extinguisher_model() uses."""
    return {"ext-" + k: v for k, v in _ext_source()["textures"].items()}


# ======================================================================== Patient monitor

def monitor(on):
    """A vital-signs monitor on a wheeled stand, its screen to the north and tilted down a little: a five-castor base
    with a wire basket of cuffs and leads, the pole, a tilting mount, the case with a dark bezel and a screen (on: the
    traces glow, nothing else), a carry handle over it, a parameter module rack on its side, and the coloured ECG leads
    looping down from it."""
    from gen_14_props_a import five_star as _five
    els = _five("Base", tex="p-darksteel")
    els += rod("Pole", "y", 8, 8.6, 0.5, 2.0, 9.6, "p-chrome")
    els += [B("Basket", (5, 5.0, 8.9), (11, 7.2, 11.6), "p-chrome", faces=no("up")),
            B("BasketIn", (5.3, 6.6, 9.2), (10.7, 6.9, 11.3), "p-darkplastic", faces=("up",)),
            B("Cuff", (5.6, 6.9, 9.4), (8.6, 7.9, 11.1), "p-liqblue"),
            B("Mount", (6.6, 9.6, 7.6), (9.4, 10.6, 9.8), "p-darksteel")]
    head = [B("Case", (2.2, 10.6, 6.2), (13.8, 16.6, 10.6), {"all": "p-greyplastic", "front": "p-greyplastic"}),
            B("CaseBack", (3.4, 11.4, 10.6), (12.6, 15.8, 11.6), "p-greyplastic"),
            B("Bezel", (2.5, 10.9, 5.95), (13.5, 16.3, 6.2), "p-darkplastic", faces=no("south")),
            pic(B("Screen", (3.1, 11.5, 5.85), (11.2, 15.7, 5.95), "p-black", faces=("north",)), "north",
                "p-monitoron" if on else "p-monitoroff", glow=200 if on else 0),
            B("Knob", (11.9, 12.0, 5.5), (12.9, 13.0, 5.95), "p-greyplastic"),
            B("Power", (11.9, 14.2, 5.65), (12.9, 15.0, 5.95), "p-liqred" if on else "p-darkplastic", glow=220 if on else 0),
            B("HandleL", (3.2, 16.6, 8.1), (4.0, 17.6, 8.9), "p-darkplastic"),
            B("HandleR", (12.0, 16.6, 8.1), (12.8, 17.6, 8.9), "p-darkplastic"),
            B("Handle", (3.2, 17.6, 8.0), (12.8, 18.3, 9.0), "p-darkplastic"),
            B("Rack", (13.8, 11.0, 6.8), (15.2, 16.0, 10.0), "p-beige-side"),
            B("ModuleA", (15.2, 11.4, 7.1), (15.4, 13.4, 9.7), "p-greyplastic", faces=("east",)),
            B("ModuleB", (15.2, 13.8, 7.1), (15.4, 15.6, 9.7), "p-liqblue", faces=("east",)),
            B("Port", (14.2, 10.4, 7.4), (15.0, 11.0, 9.4), "p-darkplastic")]
    els += turned(head, rx=8, origin=(8, 10.6, 8.6))
    # the leads: out of the module rack, down the side and looping back over the basket
    for i, (dz, tex) in enumerate(((7.6, "p-liqred"), (8.4, "p-white"), (9.2, "p-liqgreen"))):
        els += [B(f"Lead{i}", (14.6 + i * 0.15, 4.2 + i * 0.6, dz), (14.85 + i * 0.15, 10.4, dz + 0.25), tex),
                B(f"LeadLoop{i}", (9.5 + i * 0.4, 4.0 + i * 0.6, dz), (14.85 + i * 0.15, 4.25 + i * 0.6, dz + 0.25), tex)]
    return els


# ======================================================================== The lift (tools/gen_14.py)

def lift_textures(G):
    """The lift's textures (written by gen_14's save as l14 surfaces): the doors' brushed steel with a darker edge, the
    indicator panel (floor numbers and arrows, all dead), an OUT OF ORDER notice."""
    img = M.brushed_metal(seed=14700, base=(170, 174, 178), direction="v", streak=6, sheen=12)
    M.grime(img, 0.1, seed=14701, color=(90, 86, 76), cells=(8, 4), bias="bottom")
    M.scratches(img, 5, seed=14702, light=0.14, angle=0)
    G.save(img, "lift-door")
    img = M.noise_hv((26, 28, 30), 1, 14703, S, 2, (8, 4))
    d = ImageDraw.Draw(img)
    for i, n in enumerate(("B", "1", "2", "3", "4")):
        G.draw_text(img, (2 + i * 5, 10, 6 + i * 5, 17), n, (70, 60, 40), 6)
    d.polygon([(24, 16), (27, 11), (30, 16)], fill=(60, 50, 34, 255))
    d.polygon([(24, 19), (27, 24), (30, 19)], fill=(60, 50, 34, 255))
    G.save(img, "lift-indicator")
    img = TX.pic((S, S), (232, 228, 206))[0]
    img = M.paper(seed=14704, base=(232, 228, 206)) if hasattr(M, "paper") else img
    G.draw_text(img, (2, 4, 30, 14), "OUT OF\nORDER", (30, 30, 30), 6, condensed=True)
    G.draw_text(img, (3, 18, 29, 28), "USE STAIRS", (150, 30, 30), 4, condensed=True)
    G.save(img, "lift-notice")


def lift_model(half, part):
    """One block of the lift, facing north (the hall to the north): the wall behind (its own paint), the recess with the
    door leaf (its meeting edge on the block edge it shares with the other half), the steel jamb on its outer edge, the
    sill (lower), the call panel on the right jamb (upper), the head with the indicator over the doors' meeting (header).
    Seen from the hall, l is the left half: its outer edge is east (+x), its meeting edge west."""
    outer_lo, outer_hi = (14, 16) if half == "l" else (0, 2)
    leaf_lo, leaf_hi = (0, 14) if half == "l" else (2, 16)
    wall = "wall-paint"
    els = [B("Wall", (0, 0, 2), (16, 16, 16), wall)]
    if part in ("lower", "upper"):
        els += [B("Recess", (leaf_lo, 0, 1.6), (leaf_hi, 16, 2), "p-darksteel", faces=("north",)),
                B("Leaf", (leaf_lo, 0, 1.0), (leaf_hi, 16, 1.6), "lift-door", faces=("north", "up", "down")),
                B("Jamb", (outer_lo, 0, 0), (outer_hi, 16, 2), "p-steel", faces=no("south"))]
        # the leaves' meeting: a dark rubber edge on the meeting side
        mx = (0, 0.4) if half == "l" else (15.6, 16)
        els.append(B("Meet", (mx[0], 0, 0.9), (mx[1], 16, 1.6), "p-rubber", faces=("north",)))
        if part == "lower":
            els += [B("Sill", (0, 0, -0.4), (16, 0.35, 1.2), "p-steel", faces=no("south")),
                    B("Kick", (leaf_lo + 0.5, 0.35, 0.85), (leaf_hi - 0.5, 3.0, 1.0), "p-darksteel", faces=("north",))]
        else:
            if half == "l":
                els.append(pic(B("Notice", (4, 3, 0.9), (11.5, 10.5, 1.0), "p-papers", faces=("north",)), "north", "lift-notice"))
                els.append(B("Tape", (6.5, 10.2, 0.85), (9.0, 11.0, 0.95), "p-papers", faces=("north",)))
            else:
                els += [B("CallPlate", (0.25, 2.0, -0.3), (1.75, 7.5, 0), "p-steel"),
                        B("CallUp", (0.6, 5.0, -0.55), (1.4, 5.8, -0.3), "p-darkplastic"),
                        B("CallDown", (0.6, 3.4, -0.55), (1.4, 4.2, -0.3), "p-darkplastic")]
    else:
        els = [B("Wall", (0, 0, 0), (16, 16, 16), wall),
               B("Head", (0, 0, -0.3), (16, 3.0, 0), "p-steel", faces=no("south")),
               B("JambTop", (outer_lo, 3.0, -0.3), (outer_hi, 4.0, 0), "p-steel", faces=no("south"))]
        ix = (0, 6.5) if half == "l" else (9.5, 16)
        el = B("Indicator", (ix[0], 4.5, -0.6), (ix[1], 8.5, 0), "p-darksteel", faces=no("south"))
        # the panel's face across the two blocks: l (the left half seen from the hall) the picture's left half
        pic(el, "north", "lift-indicator", uv=(0, 4, 8, 13) if half == "l" else (8, 4, 16, 13))
        els.append(el)
    return els


# ======================================================================== Staff lockers

def clip_y(els, part):
    """The lower (y 0-16) or upper (y 16-32, moved down) half of a two-block-high model. Boxes across y 16 are cut there
    (losing the face at the cut); a box may be turned about y only (that leaves its height alone)."""
    import json
    lo, hi, shift = (0, 16, 0) if part == "lower" else (16, 99, -16)
    out = []
    for e in els:
        y1, y2 = e["from"][1], e["to"][1]
        if y2 <= lo + 1e-6 or y1 >= hi - 1e-6:
            continue
        assert not any(k in e for k in ("rotationX", "rotationZ")), e["name"]
        e = json.loads(json.dumps(e))
        if y1 < lo:
            e["from"][1] = lo
            e["faces"].pop("down", None)
        if y2 > hi:
            e["to"][1] = hi
            e["faces"].pop("up", None)
        (x1, a, z1), (x2, b, z2) = e["from"], e["to"]
        for f, face in e["faces"].items():
            if f in ("north", "south", "east", "west"):
                w = (x2 - x1) if f in ("north", "south") else (z2 - z1)
                face["uv"] = [face["uv"][0], 0, face["uv"][2], round(min(16, max(b - a, 0.5)), 4)] if face["uv"][1] == 0 else face["uv"]
        e["from"][1] = round(e["from"][1] + shift, 4)
        e["to"][1] = round(e["to"][1] + shift, 4)
        if "rotationOrigin" in e:
            e["rotationOrigin"][1] = round(e["rotationOrigin"][1] + shift, 4)
        out.append(e)
    return out


def locker_textures():
    sd = TX.seed_of
    img = M.painted_metal(seed=sd("lockersteel"), base=(112, 128, 120), panel=False, chips=5, under=(96, 84, 72))
    M.rust(img, 0.12, seed=sd("lockersteelR"), color=RUST, dark=RUSTDARK, pits=True, cells=(8, 4))
    M.grime(img, 0.14, seed=sd("lockersteelG"), color=(70, 66, 54), cells=(8, 4))
    TX.save(img, "lockersteel")
    img = M.painted_metal(seed=sd("lockerdoor"), base=(118, 134, 126), panel=False, chips=3, under=(96, 84, 72))
    M.scratches(img, 5, seed=sd("lockerdoorS"), light=0.14)
    M.grime(img, 0.1, seed=sd("lockerdoorG"), color=(70, 66, 54), cells=(8, 4), bias="bottom")
    TX.save(img, "lockerdoor")


def locker_model(ajar_left):
    """A pair of staff lockers two blocks high (y 0-32), fronts to the north: a plinth, the carcass, two doors with louvres
    top and bottom, a latch handle and a number tab each, a padlock on one; ajar_left: the left door (seen from the
    front: +x) swung open on its hinge, a work shirt on a hook and a shelf inside."""
    S_, D = "p-lockersteel", "p-darksteel"
    els = [B("Plinth", (0.2, 0, 3.4), (15.8, 1.4, 15.8), D),
           B("BodyR", (0, 1.4, 3.0), (8, 30.4, 16), S_),
           B("Cap", (-0.2, 30.4, 2.6), (16.2, 31.2, 16), S_),
           B("Divider", (7.8, 1.4, 2.7), (8.2, 30.4, 3.0), D, faces=no("south"))]
    if ajar_left:
        # the open locker's carcass: its back, outer side, floor and roof, dark inside
        els += [B("BackL", (8, 1.4, 15.2), (16, 30.4, 16), {"all": S_, "north": "p-black"}),
                B("SideL", (15.4, 1.4, 3.0), (16, 30.4, 15.2), {"all": S_, "west": "p-black"}),
                B("FloorL", (8, 1.4, 3.0), (15.4, 1.9, 15.2), {"all": S_, "up": "p-darksteel"}),
                B("RoofL", (8, 29.9, 3.0), (15.4, 30.4, 15.2), {"all": S_, "down": "p-black"}),
                B("WallL", (8, 1.9, 3.0), (8.4, 29.9, 15.2), {"all": S_, "east": "p-black"})]
    else:
        els.append(B("BodyL", (8, 1.4, 3.0), (16, 30.4, 16), S_))
    for i, x in enumerate((0, 8)):
        left = i == 1  # seen from the front, +x is the left
        door = [B(f"Door{i}", (x + 0.35, 1.7, 2.6), (x + 7.65, 30.1, 3.0), "p-lockerdoor", faces=no("south"))]
        for j, y in enumerate((25.0, 25.9, 26.8, 27.7, 3.2, 4.1, 5.0)):
            door.append(B(f"Louvre{i}{j}", (x + 1.6, y, 2.3), (x + 6.4, y + 0.5, 2.6), D, faces=no("south")))
        hx = x + 1.0 if left else x + 6.0
        door += [B(f"Latch{i}", (hx, 14.0, 2.15), (hx + 1.0, 17.2, 2.6), "p-chrome"),
                 B(f"Tab{i}", (x + 2.6, 21.0, 2.45), (x + 5.4, 22.3, 2.6), "p-brass")]
        if i == 0:
            door += [B("Padlock", (hx + 0.1, 12.6, 1.8), (hx + 0.9, 13.8, 2.15), "p-brass"),
                     B("Shackle", (hx + 0.25, 13.8, 1.9), (hx + 0.75, 14.5, 2.05), "p-chrome")]
        if left and ajar_left:
            # swung open about its hinge on the outer (+x) edge
            door = turned(door, ry=-38, origin=(x + 7.65, 0, 2.8))
            els += [B("Shelf", (x + 0.4, 25.5, 3.2), (x + 7.4, 26.0, 15.2), D, faces=("up", "north", "down")),
                    B("Hook", (x + 3.6, 23.0, 13.6), (x + 4.4, 24.6, 15.4), "p-chrome"),
                    B("Shirt", (x + 1.4, 12.0, 12.2), (x + 6.6, 23.2, 14.2), "p-blanket-side"),
                    B("Shoes", (x + 1.0, 1.4, 5.0), (x + 7.0, 3.2, 10.0), "p-leather")]
        els += door
    return els


def locker(part, ajar):
    return clip_y(locker_model(ajar), part)
