"""Textures for Level 4's props rebuilt as geometry (graphics pass, "Level 4 art": dead ficus, reception desk, coat stand,
stacked chairs, wall clock, office door, drinking fountain, the windows).

Called from `detail_textures.level4`. Every key here is new and starts with `l4`: the old shared keys (`wood`, `steel`,
`coat`, `plasticchair`, `foldsteel`, `clockface`...) are also used by other levels' props and stay as they were.
Each model part's face shows its texture from the corner (UV from the part's own size), so wear is scattered and printed
art sits in the top-left of the 32x32 texture, 2 px per unit of the part. Lettering is the 3x5 pixel face of
`l1props_tex.FONT`, crisp, never scaled type.
"""
import math
import random

import matlib as M
from PIL import Image, ImageDraw

from detail_kit import T, seed_of
from l1props_tex import FONT, word, word_width

S = 32


def save(img, name):
    T.save(img, f"block/detail/{name}.png")


def rgb(c, a=255):
    return tuple(c) + (a,)


def solid(c, a=255):
    return Image.new("RGBA", (S, S), rgb(c, a))


def ficus():
    """Bark, leaves (dry, in several tones), a ceramic pot, dry soil."""
    img = M.noise_hv((104, 84, 62), 3, seed_of("l4bark"), S, 5, (16, 8), hue=1.5)
    px = img.load()
    rng = random.Random(seed_of("l4bark"))
    for x in range(0, S, 1):  # vertical fissures
        if rng.random() < 0.28:
            y0, ln = rng.randrange(S), rng.randint(6, 14)
            for k in range(ln):
                px[x, (y0 + k) % S] = M.rgba(M.lift(px[x, (y0 + k) % S], -22))
                px[(x + 1) % S, (y0 + k) % S] = M.rgba(M.lift(px[(x + 1) % S, (y0 + k) % S], 8))
    save(img, "l4bark")
    # leaves: each box is one leaf, drawn from the corner: a lit midrib along the middle, darker rim, brittle tones
    for i, base in enumerate(((120, 104, 54), (140, 108, 58), (104, 86, 46), (152, 120, 66), (92, 94, 48), (126, 94, 52))):
        img = M.noise_hv(base, 4, seed_of(f"l4leaf{i}"), S, 5, (16, 8), hue=2)
        px = img.load()
        for y in range(S):
            px[3, y] = M.rgba(M.lift(px[3, y], 14))
            px[4, y] = M.rgba(M.lift(px[4, y], 6))
        save(img, f"l4leaf{i}")
    img = M.noise_hv((226, 220, 206), 3, seed_of("l4pot"), S, 3, (16, 8), hue=0.8)
    M.grime(img, 0.18, seed_of("l4potgrime"), color=(150, 138, 112), cells=(8, 4), cover=0.5)
    save(img, "l4pot")
    img = M.noise_hv((62, 46, 34), 6, seed_of("l4soil"), S, 7, (8, 4), hue=1.5)
    px = img.load()
    rng = random.Random(seed_of("l4soil"))
    for _ in range(40):  # dry crust cracks and grit
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = M.rgba(M.lift(px[x, y], rng.choice((-20, 22))))
    save(img, "l4soil")


def reception():
    img = M.wood_planks(seed_of("l4veneer"), base=(132, 92, 56), planks=1, direction="v", grain=3, contrast=0.8, per_plank=4, flecks=0.8)
    save(img, "l4veneer")
    img = M.noise_hv((92, 86, 80), 4, seed_of("l4counter"), S, 4, (16, 8), hue=1.2)
    px = img.load()
    rng = random.Random(seed_of("l4counter"))
    for _ in range(70):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = M.rgba(M.lift(px[x, y], rng.choice((-16, 16))))
    M.grime(img, 0.1, seed_of("l4counterwear"), color=(120, 112, 100), cells=(8, 4), cover=0.4)
    save(img, "l4counter")
    save(M.noise_hv((44, 34, 28), 3, seed_of("l4edge"), S, 3, (16, 8)), "l4edge")  # dark edge banding
    save(M.noise_hv((34, 34, 36), 3, seed_of("l4kick"), S, 2, (16, 8)), "l4kick")
    # a brass-edged plate: WELCOME (7 letters, 27 px) in the pixel face, on a 28 px plate (14 units)
    img = M.brushed_metal(seed_of("l4plate"), base=(176, 150, 92), grain=3, direction="h", streak=6, sheen=6)
    word(img, "WELCOME", 2, 2, (44, 32, 18))
    save(img, "l4recplate")
    img = M.noise_hv((214, 206, 188), 3, seed_of("l4ledger"), S, 3, (16, 8))
    px = img.load()
    for y in range(3, S - 2, 3):
        for x in range(2, S - 2):
            px[x, y] = M.rgba((150, 156, 170))
    save(img, "l4ledger")


def coatstand():
    img = M.wood_planks(seed_of("l4stand"), base=(78, 50, 30), planks=1, direction="v", grain=3, contrast=0.7, per_plank=3, flecks=0.6)
    save(img, "l4stand")
    img = M.fabric(seed_of("l4coat"), base=(62, 64, 70), weave="twill", contrast=8, grain=3, mottle=5, thread=3)
    px = img.load()
    for y in range(S):  # a soft fold
        for x in range(S):
            if x % 11 == 4:
                px[x, y] = M.rgba(M.lift(px[x, y], -10))
    save(img, "l4coat")
    save(M.fabric(seed_of("l4scarf"), base=(120, 50, 46), weave="plain", contrast=10, grain=3, mottle=4, thread=3), "l4scarf")
    save(M.fabric(seed_of("l4lining"), base=(110, 86, 64), weave="plain", contrast=6, grain=2, mottle=3, thread=2), "l4lining")
    save(M.brushed_metal(seed_of("l4hanger"), base=(160, 156, 148), grain=3, streak=6, sheen=6), "l4hanger")
    save(M.noise_hv((36, 34, 32), 3, seed_of("l4button"), S, 2, (16, 8)), "l4button")


def chairs():
    img = M.noise_hv((96, 112, 134), 3, seed_of("l4shell"), S, 3, (16, 8), hue=1.2)
    M.grime(img, 0.1, seed_of("l4shellgrime"), color=(130, 124, 112), cells=(8, 4), cover=0.4)
    px = img.load()
    for y in range(S):  # a soft moulded sheen
        for x in range(S):
            if (x + y) % 32 in (14, 15):
                px[x, y] = M.rgba(M.lift(px[x, y], 6))
    save(img, "l4shell")
    save(M.brushed_metal(seed_of("l4tube"), base=(138, 140, 142), grain=3, direction="v", streak=6, sheen=8), "l4tube")
    save(M.noise_hv((30, 30, 32), 2, seed_of("l4foot"), S, 2, (16, 8)), "l4foot")


def clock():
    """A wall clock's dial 32 px over 8 units (4 px per unit): white card, black ring, ticks, numerals in the pixel face
    (12 3 6 9 large, the rest as ticks), the glass a cut-out with two short glints, and the black case."""
    img = Image.new("RGBA", (S, S), rgb((30, 30, 32)))
    d = ImageDraw.Draw(img)
    cx = cy = 15.5
    d.ellipse([1, 1, 30, 30], fill=rgb((238, 234, 222)))
    px = img.load()
    for a in range(60):
        ang = math.radians(a * 6)
        r1, r2 = (11.5, 13.8) if a % 5 == 0 else (13, 13.8)
        x1, y1 = cx + r1 * math.sin(ang), cy - r1 * math.cos(ang)
        x2, y2 = cx + r2 * math.sin(ang), cy - r2 * math.cos(ang)
        d.line([x1, y1, x2, y2], fill=rgb((30, 30, 32)))
    for s, x, y in (("12", 12, 5), ("3", 22, 13), ("6", 14, 21), ("9", 6, 13)):
        word(img, s, x, y, (30, 30, 32))
    for y in range(S):  # age: the card yellowed toward the ring
        for x in range(S):
            if (x - cx) ** 2 + (y - cy) ** 2 < 15 ** 2:
                dd = math.hypot(x - cx, y - cy) / 15
                px[x, y] = M.rgba(M.mix(px[x, y][:3], (222, 208, 170), 0.35 * dd * dd))
    save(img, "l4clockface")
    save(M.noise_hv((30, 30, 33), 3, seed_of("l4clockcase"), S, 2, (16, 8)), "l4clockcase")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    for k in range(5):  # a short glint up the top left of the glass
        px[5 + k, 4 + (k // 2)] = M.rgba((226, 230, 232))
    px[4, 6] = px[4, 7] = M.rgba((206, 212, 216))
    save(img, "l4clockglass")


def door():
    """The office door: a flush veneer leaf (the cube; no painted hardware), the steel frame and its stiles, a brushed
    lever and lock set, the ROOM plate, the vision strip's dark glass."""
    for part in ("lower", "upper"):
        img = M.wood_planks(seed_of("l4leaf" + part), base=(152, 112, 70), planks=1, direction="v", grain=3, contrast=0.9,
                            per_plank=5, flecks=0.9)
        save(img, f"officedoor-{part}")
    save(M.painted_metal(seed_of("l4doorframe"), base=(126, 130, 134), grain=3, mottle=2, panel=False, chips=2, under=(150, 150, 148)), "l4doorframe")
    save(M.brushed_metal(seed_of("l4lever"), base=(196, 198, 200), grain=3, direction="h", streak=6, sheen=8), "l4lever")
    save(M.noise_hv((36, 38, 40), 3, seed_of("l4doorlock"), S, 2, (16, 8)), "l4lockface")
    img = M.noise_hv((46, 58, 66), 3, seed_of("l4doorglass"), S, 4, (16, 8), hue=1.5)  # the dark room behind
    px = img.load()
    for y in range(S):
        for x in range(S):
            if (x + y) % 20 in (7, 8) and y < 22:
                px[x, y] = M.rgba(M.lift(px[x, y], 14))
    save(img, "l4doorglass")
    img = M.brushed_metal(seed_of("l4roomplate"), base=(188, 190, 188), grain=3, direction="h", streak=6, sheen=6)
    word(img, "ROOM", 2, 2, (30, 30, 32))
    save(img, "l4roomplate")
    save(M.brushed_metal(seed_of("l4kickplate"), base=(150, 152, 154), grain=3, direction="h", streak=6, sheen=8), "l4kickplate")


def fountain():
    save(M.brushed_metal(seed_of("l4fsteel"), base=(188, 192, 196), grain=3, direction="h", streak=7, sheen=8), "l4fsteel")
    save(M.brushed_metal(seed_of("l4fsteelv"), base=(176, 180, 184), grain=3, direction="v", streak=7, sheen=8), "l4fsteelv")
    save(M.noise_hv((58, 62, 66), 3, seed_of("l4fdrain"), S, 3, (16, 8)), "l4fdrain")
    save(M.noise_hv((150, 156, 160), 3, seed_of("l4fwet"), S, 3, (16, 8)), "l4fbowl")
    save(M.noise_hv((22, 24, 26), 2, seed_of("l4fblack"), S, 2, (16, 8)), "l4fblack")


def windows():
    """The shut windows: a satin-aluminium frame, and in it the pane painted out black (matte, a few brush strokes), with
    torn strips of black paper and masking tape holding it. The blinds: slats in three states."""
    save(M.painted_metal(seed_of("l4winframe"), base=(168, 168, 164), grain=3, mottle=2, panel=False, chips=2, under=(128, 126, 120)), "l4winframe")
    img = M.noise_hv((16, 16, 17), 2, seed_of("l4blackpane"), S, 2, (16, 8), hue=0.5)
    px = img.load()
    rng = random.Random(seed_of("l4blackpane"))
    for _ in range(10):  # brush strokes, each a slightly different black
        y, x0, ln = rng.randrange(S), rng.randrange(S), rng.randint(10, 24)
        for k in range(ln):
            px[(x0 + k) % S, y] = M.rgba(M.lift(px[(x0 + k) % S, y], rng.choice((3, 4, 5))))
    save(img, "l4blackpane")
    img = M.noise_hv((200, 186, 150), 3, seed_of("l4tape"), S, 3, (16, 8))  # masking tape
    save(img, "l4tape")


def blinds_tex(state, seed):
    """(blind window, a cube) the whole block: aluminium head and frame, the slats (3 px pitch: a lit rounded top, the
    slat, a dark gap), ladder cords, a bottom rail with a pull. `state`: 'down' slats shut to the sill; 'half' drawn up
    to half height, dark glass above with a faint grey light; 'tilt' slats opened with grey light between."""
    rng = random.Random(seed_of("blinds" + state + str(seed)))
    base = (196, 192, 182) if seed != 2 else (184, 182, 176)
    img = Image.new("RGBA", (S, S), rgb((36, 40, 44)))
    px = img.load()
    glass = M.noise_hv((46, 52, 58), 3, seed_of("l4blindglass"), S, 3, (16, 8), hue=1.5)
    gp = glass.load()
    top = 2
    bottom = S - 2
    cut = {"down": top, "half": 15, "tilt": top}[state]  # first row of the slats
    for y in range(top, bottom):
        for x in range(2, S - 2):
            if y < cut:
                px[x, y] = gp[x, y]
                continue
            k = (y - cut) % 3
            if state == "tilt":
                c = (M.lift(base, 8), M.lift(base, -14), (88, 94, 100))[k]
            else:
                c = (M.lift(base, 14), M.lift(base, 0), M.lift(base, -28))[k]
            px[x, y] = M.rgba(M.lift(c, rng.uniform(-2, 2)))
    for x in (8, 23):  # the ladder cords
        for y in range(top if state != "half" else cut - 1, bottom):
            px[x, y] = M.rgba(M.lift((226, 224, 214), 4 if (y - cut) % 3 == 0 else -6))
    if state == "half":  # the bottom rail of the raised blind, and its cord's tassel
        for x in range(2, S - 2):
            px[x, cut - 1] = M.rgba((140, 138, 130))
            px[x, cut - 2] = M.rgba((120, 118, 112)) if x % 2 else M.rgba((126, 124, 116))
        for y in range(cut, cut + 5):
            px[24, y] = M.rgba((236, 232, 220))
    else:  # the rail at the bottom
        for x in range(2, S - 2):
            px[x, bottom - 2] = M.rgba((150, 148, 140))
            px[x, bottom - 1] = M.rgba((112, 110, 104))
    # the aluminium frame
    frame = (160, 160, 156)
    for i in range(S):
        for (x, y) in ((i, 0), (i, 1), (0, i), (1, i), (i, S - 1), (i, S - 2), (S - 1, i), (S - 2, i)):
            px[x, y] = M.rgba(M.lift(frame, rng.uniform(-2, 2) + (6 if y == 0 or x == 0 else -6 if y >= S - 2 or x >= S - 2 else 0)))
    for i in range(2, S - 2):
        px[i, 2] = M.rgba(M.lift(px[i, 2][:3], -14))
        px[2, i] = M.rgba(M.lift(px[2, i][:3], -8))
    return img



# ---- (play-test, layout 11) Level 4's windows as whole panes ----
# A pane is two blocks tall (from the drywall base to the ceiling) and two wide, or one wide at the end of a run. Each
# is drawn whole, then cut into its blocks: officepane-<kind>-<l|r|s>-<lower|upper>, the left or right half as seen
# from outside the face, or "s" for a pane one block wide. Same frame, glass and slats as the one-block windows.

PANE_H = 2 * S


def pane_frame(img, seed):
    """The satin-aluminium frame round a whole pane only: head and jambs 2 px, the sill 3 px with its lit top edge; lit
    along the head and the left jamb, shaded along the right jamb and the sill's face, and the glass in the frame's
    shadow under the head and beside the left jamb."""
    w, h = img.size
    px = img.load()
    rng = random.Random(seed)
    frame = (154, 156, 154)
    for x in range(2, w - 2):  # the frame's shadow on the glass, under the head and inside the left jamb
        px[x, 2] = M.rgba(M.lift(px[x, 2][:3], -16))
    for y in range(2, h - 3):
        px[2, y] = M.rgba(M.lift(px[2, y][:3], -10))
        px[w - 3, y] = M.rgba(M.lift(px[w - 3, y][:3], -5))
    for y in range(h):
        for x in range(w):
            if y <= 1:
                d = 8
            elif y >= h - 3:
                d = 12 if y == h - 3 else -10
            elif x <= 1:
                d = 8
            elif x >= w - 2:
                d = -10
            else:
                continue
            px[x, y] = M.rgba(M.lift(frame, rng.uniform(-2, 2) + d))
    return img


def clear_pane(w, seed):
    """The clear window as one sheet: dark cold glass, nothing to see through it, a faint reflection of the strip
    lights (one pale bar in a narrow pane, two in a wide one) and soft smudges of old condensation."""
    img = M.noise_hv((58, 64, 72), 2, seed, (w, PANE_H), 5, (16, 8), hue=1.5)
    px = img.load()
    rng = random.Random(seed + 1)
    for _ in range(3 * w // S + 1):
        cx, cy, r = rng.randrange(4, w - 4), rng.randrange(4, PANE_H - 5), rng.randint(2, 4)
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                d = math.hypot(x - cx, y - cy)
                if d <= r and 3 <= x < w - 3 and 3 <= y < PANE_H - 4:
                    px[x, y] = M.rgba(M.lift(px[x, y], 7 * (1 - d / r)))
    for x0, lift in ([(7, 5)] if w == S else [(13, 5), (44, 3)]):
        for y in range(3, PANE_H - 3):
            for x in (x0, x0 + 1):
                px[x, y] = M.rgba(M.lift(px[x, y], lift))
    return pane_frame(img, seed + 2)


def blinds_pane(state, w, seed):
    """Venetian blinds the width of the pane, hung from one headrail: 'down' shut to the sill, 'half' drawn up to half
    the window's height (its bottom rail level across the pane, dark glass below with a faint grey light), 'tilt' down
    with the slats opened. Slats 3 px pitch (a lit rounded top, the slat, a dark gap), ladder cords every ~16 px of
    width, and a pull cord with its tassel at the right."""
    rng = random.Random(seed_of("pane" + state) + w)
    base = (196, 192, 182) if state != "tilt" else (184, 182, 176)
    img = M.noise_hv((46, 52, 58), 3, seed_of("l4paneglass") + w, (w, PANE_H), 3, (16, 8), hue=1.5)
    px = img.load()
    x0, x1 = 2, w - 2
    head = 2  # the headrail: rows 2-4
    sill = PANE_H - 3
    rail = {"down": sill - 2, "half": 37, "tilt": sill - 2}[state]  # first row of the bottom rail (two rows)
    for y in range(head + 3, rail):
        k = (y - head - 3) % 3
        for x in range(x0, x1):
            if state == "tilt":
                c = (M.lift(base, 8), M.lift(base, -14), (88, 94, 100))[k]
            else:
                c = (M.lift(base, 14), M.lift(base, 0), M.lift(base, -28))[k]
            px[x, y] = M.rgba(M.lift(c, rng.uniform(-2, 2)))
    cords = (8, 23) if w == S else (11, 32, 52)
    for x in cords:  # the ladder cords, down the slats to the bottom rail
        for y in range(head + 3, rail):
            px[x, y] = M.rgba(M.lift((226, 224, 214), 4 if (y - head - 3) % 3 == 0 else -6))
    for x in range(x0, x1):
        px[x, head] = M.rgba(M.lift((210, 206, 196), 10 + rng.uniform(-2, 2)))  # the headrail, lit along its top
        px[x, head + 1] = M.rgba(M.lift((204, 200, 190), rng.uniform(-2, 2)))
        px[x, head + 2] = M.rgba(M.lift((204, 200, 190), -30))  # its shadow
        px[x, rail] = M.rgba((150, 148, 140))  # the bottom rail
        px[x, rail + 1] = M.rgba((112, 110, 104) if x % 2 else (118, 116, 108))
    if state == "half":  # the glass under the raised blind, a little lighter where the grey day comes in
        for y in range(rail + 2, sill):
            for x in range(x0, x1):
                px[x, y] = M.rgba(M.lift(px[x, y][:3], 3))
    cx = w - 6  # the pull cord from the headrail, past the bottom rail, ending in a tassel
    end = 44
    for y in range(head + 3, end):
        px[cx, y] = M.rgba(M.lift((232, 228, 216), -6 if y % 2 else 0))
    for y in range(end, end + 3):
        for x in (cx - 1, cx, cx + 1) if y > end else (cx,):
            px[x, y] = M.rgba(M.lift((236, 232, 220), -12 if x != cx else 0))
    return pane_frame(img, seed_of("paneframe" + state) + w)


def save_pane(img, name):
    """A whole pane cut into its blocks: the left and right halves of a wide one, upper and lower."""
    w = img.width
    halves = [("s", 0)] if w == S else [("l", 0), ("r", S)]
    for half, x in halves:
        for part, y in (("upper", 0), ("lower", S)):
            save(img.crop((x, y, x + S, y + S)), f"officepane-{name}-{half}-{part}")


def panes():
    for w in (S, 2 * S):
        save_pane(clear_pane(w, seed_of("l4paneclear")), "clear")
        for state in ("down", "half", "tilt"):
            save_pane(blinds_pane(state, w, seed_of("l4paneblinds")), state)

def generate():
    ficus()
    reception()
    coatstand()
    chairs()
    clock()
    door()
    fountain()
    windows()
    for i, (state, seed) in enumerate((("down", 0), ("half", 1), ("tilt", 2), ("half", 3))):
        save(blinds_tex(state, seed), "officewindow-blinds" + ("" if i == 0 else f"-{i + 1}"))
    panes()
