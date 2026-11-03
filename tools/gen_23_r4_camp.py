"""Level 23, round 4 (2026-11-02): Base Seedling's things rebuilt to the asset bar, called from tools/gen_23.py.

- `l23-tent-<part>-<side>`: the M.E.G.'s canvas wall tent, two blocks by two (the layout's Props.CampTent tiles; similar to
  the detail kit's `camptent`, re-detailed as an expedition's wall tent): canvas walls, a pitched fly on a ridge pole,
  the door flaps tied back, guy lines to pegs, a stovepipe through the roof, M.E.G. 23-1 stencilled by the door; inside
  a cot, a footlocker and the stove.
- `l23-campbarrel`, `l23-campcrate` (models replacing round 3's barrel and the cube crate): staves and two iron hoops,
  a lid and a brass tap, WATER on a flat label; a crate of boards with battens, corner irons and a lid.
- `l23-campfire`: the fire ring with stones, ash, crossed charred logs, embers glowing, a tripod with a pot hanging.
- `l23-campbed-<side>`: a bedroll (mat, sleeping bag turned back, pillow, a strapped roll at the foot).
- `l23-camplamp`: the M.E.G.'s hurricane lantern (fount, wire guard, glowing globe, chimney, bail).
- `l23-counter-<part>-<side>`: the quartermaster's counter, three blocks: plank top, boarded front, a shelf under with
  tins, a balance and a cash tin on top.
Models face NORTH and have the variant group "side" last (rotateY: east 270, south 180, west 90).
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

import matlib as M
import gen_23 as G
import gen_23_r3 as R3

sys.path.insert(0, os.path.dirname(__file__))

S = G.S
SIDES = ["north", "east", "south", "west"]
ROT = {"north": 0, "east": 270, "south": 180, "west": 90}
WOOD = G.WOOD
CLOTH = {"walk": "game:walk/cloth*", "place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"}
WOODS = {"walk": WOOD[0], "place": WOOD[1], "break": WOOD[1], "hit": WOOD[1]}
METAL = {"walk": "game:walk/stone*", "place": "game:block/anvil", "break": "game:block/anvil", "hit": "game:block/anvil"}
STONES = {"walk": "game:walk/stone*", "place": "game:block/rock-hit-pickaxe", "break": "game:block/rock-hit-pickaxe", "hit": "game:block/rock-hit-pickaxe"}
T = "backrooms:block/23/"


def dflt(frm, to, face):
    """The detail kit's plain uv (the box's own size from the texture's corner, capped at a block)."""
    w, h, d = (abs(to[i] - frm[i]) for i in range(3))
    a, b = {"north": (w, h), "south": (w, h), "east": (d, h), "west": (d, h), "up": (w, d), "down": (w, d)}[face]
    return [0, 0, round(min(16, max(a, 0.5)), 3), round(min(16, max(b, 0.5)), 3)]


def bx(name, frm, to, tex, faces=("north", "east", "south", "west", "up", "down"), rot=None, origin=None, glow=0, over=None):
    """A box with plain uv on every face; over maps a face to (texture, uv) to override one."""
    frm = [round(v, 3) for v in frm]
    to = [round(v, 3) for v in to]
    fs = {}
    for f in faces:
        fs[f] = {"texture": "#" + tex, "uv": dflt(frm, to, f)}
        if glow:
            fs[f]["glow"] = glow
    for f, (t, uv) in (over or {}).items():
        fs[f] = {"texture": "#" + t, "uv": uv}
        if glow:
            fs[f]["glow"] = glow
    e = {"name": name, "from": frm, "to": to, "faces": fs}
    if rot:
        e["rotationOrigin"] = list(origin)
        for k, a in zip(("rotationX", "rotationY", "rotationZ"), rot):
            if a:
                e[k] = round(a, 3)
    return e


def shape(textures, elements):
    keys = {f["texture"][1:] for e in elements for f in e["faces"].values()}
    return {"textureWidth": 16, "textureHeight": 16, "textures": {k: T + textures[k] if ":" not in textures[k] else textures[k] for k in sorted(keys)},
            "elements": elements}


def shift(els, dx=0, dz=0):
    out = []
    for e in els:
        e = dict(e)
        e["from"] = [e["from"][0] + dx, e["from"][1], e["from"][2] + dz]
        e["to"] = [e["to"][0] + dx, e["to"][1], e["to"][2] + dz]
        if "rotationOrigin" in e:
            o = e["rotationOrigin"]
            e["rotationOrigin"] = [o[0] + dx, o[1], o[2] + dz]
        out.append(e)
    return out


def split(els, width, depth):
    """Cuts a model of width x depth blocks into one per block (the detail kit's way: gen_detail.split_blocks)."""
    import gen_detail
    return gen_detail.split_blocks(els, width, depth)


# ---------------- Textures ----------------

def canvas_wall(seed, base=(112, 110, 76)):
    """Olive canvas, a heavy basket weave, mud splashed up its foot and rain-darkened streaks down it."""
    img = M.fabric(seed, base=base, weave="basket", contrast=12, grain=3, mottle=7)
    M.grime(img, 0.18, seed + 1, color=(70, 58, 40))
    px = img.load()
    rng = random.Random(seed + 2)
    for y in range(S):
        for x in range(S):
            if y > 25:
                px[x, y] = M.rgba(M.mix(px[x, y][:3], (74, 62, 44), (y - 25) / 9 * rng.uniform(0.6, 1)))
    for _ in range(3):
        x = rng.randrange(S)
        for y in range(rng.randrange(8), S):
            px[x, y] = M.rgba(M.lift(px[x, y][:3], -10))
    return img


def canvas_inside(seed):
    img = canvas_wall(seed, (84, 82, 60))
    px = img.load()
    for y in range(S):
        for x in range(S):
            px[x, y] = M.rgba(M.lift(px[x, y][:3], -18))
    return img


def canvas_stencil(seed):
    """The front panel by the door: M.E.G. / 23-1 stencilled in faded white, in the panel's upper part."""
    img = canvas_wall(seed)
    R3.stencil(img, "M.E.G.", 7, colour=(214, 210, 190), y=3, alpha=255)
    R3.stencil(img, "23-1", 7, colour=(214, 210, 190), y=12, alpha=255)
    return opaque(img)


def roof_canvas(seed):
    img = canvas_wall(seed, (100, 102, 68))
    px = img.load()
    rng = random.Random(seed + 5)
    # Leaf litter and a water stain on the fly
    for _ in range(9):
        x, y = rng.randrange(S), rng.randrange(S)
        c = rng.choice([(120, 70, 40), (96, 60, 36), (140, 100, 50)])
        for dx in range(rng.randint(1, 2)):
            px[(x + dx) % S, y] = M.rgba(c)
    return img


def groundsheet(seed):
    return M.fabric(seed, base=(70, 76, 64), weave="ripstop", contrast=8)


def pole(seed):
    return M.wood_planks(seed, base=(126, 98, 66), planks=[32], direction="v", grain=3)


def rope(seed):
    return M.noise_hv((176, 160, 122), 3, seed, mottle=3)


def iron(seed):
    img = M.painted_metal(seed, base=(56, 56, 54), chips=2, under=(96, 70, 50), panel=False)
    M.rust(img, 0.18, seed + 1)
    return img


def tin(seed):
    return M.brushed_metal(seed, base=(150, 150, 146))


def brass(seed):
    return M.brushed_metal(seed, base=(170, 134, 64))


def stave(seed):
    """Barrel staves: oak boards up the barrel, dark joints between them, wear on the edges."""
    return M.wood_planks(seed, base=(124, 92, 58), planks=4, direction="v", grain=4, knots=1)


def lid(seed):
    return M.wood_planks(seed, base=(112, 84, 54), planks=4, direction="h", grain=4)


def label_water(seed):
    img = Image.new("RGBA", (S, S), (196, 186, 150, 255))
    M.grime(img, 0.2, seed)
    R3.stencil(img, "WATER", 8, colour=(40, 70, 120), y=6, alpha=255)
    R3.stencil(img, "DRINKING", 5, colour=(40, 70, 120), y=17, alpha=255)
    return opaque(img)


def crate_board(seed):
    return M.wood_planks(seed, base=(136, 108, 70), planks=3, direction="h", grain=4, knots=1)


def crate_front(seed):
    img = crate_board(seed)
    R3.stencil(img, "M.E.G.", 8, colour=(34, 32, 28), y=11, alpha=255)
    return opaque(img)


def ash(seed):
    img = M.noise_hv((92, 88, 82), 6, seed, mottle=9)
    G.flecks(img, seed + 1, 30, (40, 36, 32), 0.7)
    G.flecks(img, seed + 2, 12, (190, 186, 176), 0.5)
    return img


def flame(seed):
    img = Image.new("RGBA", (S, S))
    px = img.load()
    rng = random.Random(seed)
    for y in range(S):
        for x in range(S):
            t = y / S
            c = M.mix((255, 236, 150), (238, 110, 34), t)
            px[x, y] = M.rgba(M.lift(c, rng.uniform(-10, 10)))
    return img


def globe(seed):
    """A lit lantern's glass: a hot core where the flame is, the glass round it amber, darker toward its edges."""
    img = Image.new("RGBA", (S, S))
    px = img.load()
    rng = random.Random(seed)
    for y in range(S):
        for x in range(S):
            r = math.hypot((x + 0.5 - S / 2) / (S / 2), (y + 0.5 - S * 0.6) / (S / 2))
            c = M.mix((255, 240, 190), (196, 120, 50), min(1, r * 1.2))
            px[x, y] = M.rgba(M.lift(c, rng.uniform(-6, 6)))
    return img


def quilt(seed, base=(122, 52, 42)):
    img = M.fabric(seed, base=base, weave="plain", contrast=6)
    px = img.load()
    for y in range(S):
        for x in range(S):
            if y % 8 == 0:
                px[x, y] = M.rgba(M.lift(px[x, y][:3], -26))
    return img


def flannel(seed):
    img = M.fabric(seed, base=(170, 150, 110), weave="twill", contrast=8)
    px = img.load()
    for y in range(S):
        for x in range(S):
            if (x // 4) % 3 == 0 or (y // 4) % 3 == 0:
                px[x, y] = M.rgba(M.mix(px[x, y][:3], (120, 40, 36), 0.35))
    return img


def ledger_spine(seed):
    return M.fabric(seed, base=(60, 70, 96), weave="plain", contrast=6)


def tins_label(seed):
    img = M.painted_metal(seed, base=(150, 46, 40), chips=3, panel=False)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 10, S - 1, 21], fill=(224, 214, 180, 255))
    d.line([3, 15, 28, 15], fill=(60, 50, 40, 255))
    return img


def opaque(img):
    px = img.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255)
    return img


def textures(save):
    for name, img in [("tent-canvas", canvas_wall(2460)), ("tent-inside", canvas_inside(2461)), ("tent-stencil", canvas_stencil(2462)),
                      ("tent-fly", roof_canvas(2463)), ("tent-floor", groundsheet(2464)), ("tent-pole", pole(2465)),
                      ("rope", rope(2466)), ("iron", iron(2467)), ("tin", tin(2468)), ("brass", brass(2469)), ("stave", stave(2470)),
                      ("barrel-lid", lid(2471)), ("label-water", label_water(2472)), ("crate-board", crate_board(2473)),
                      ("crate-front", crate_front(2474)), ("ash", ash(2475)), ("flame", flame(2476)), ("globe", globe(2477)),
                      ("quilt", quilt(2478)), ("flannel", flannel(2479)), ("cover", ledger_spine(2480)), ("tins", tins_label(2481))]:
        save(opaque(img), f"block/23/{name}")


TEX = {"canvas": "tent-canvas", "inside": "tent-inside", "stencil": "tent-stencil", "fly": "tent-fly", "floor": "tent-floor",
       "pole": "tent-pole", "rope": "rope", "iron": "iron", "tin": "tin", "brass": "brass", "stave": "stave", "lid": "barrel-lid",
       "label": "label-water", "board": "crate-board", "front": "crate-front", "ash": "ash", "flame": "flame", "globe": "globe",
       "quilt": "quilt", "flannel": "flannel", "cover": "cover", "tins": "tins", "stone": "boulder", "char": "charred",
       "ember": "embers", "paper": "ledger", "plank": "planks", "blanket": "blanket", "bedcanvas": "canvas"}


# ---------------- The wall tent (two blocks by two, door north) ----------------

def wall_tent():
    W0, W1 = 1.5, 30.5      # the side walls' planes (x)
    EAVE, RIDGE = 13.0, 27.0
    Z0, Z1 = 1.0, 31.0      # front and back
    els = []
    # Side walls (canvas outside, darker inside), in two lengths so the texture keeps its scale
    for nm, x0, x1, inner in (("WallL", W0 - 0.4, W0, "east"), ("WallR", W1, W1 + 0.4, "west")):
        for k, (za, zb) in enumerate(((Z0, 16), (16, Z1))):
            e = bx(f"{nm}{k}", (x0, 0, za), (x1, EAVE, zb), "canvas", faces=("north", "east", "south", "west", "up"))
            e["faces"][inner]["texture"] = "#inside"
            els.append(e)
    # The fly: each slope from the eave (overhanging it) to the ridge, rotated about z at the wall's top
    run, rise = 16 - W0, RIDGE - EAVE
    slope = math.hypot(run, rise)
    lean = math.degrees(math.atan2(run, rise))
    for nm, x, sign in (("FlyL", W0, -1), ("FlyR", W1, 1)):
        for k, (y1, y2) in enumerate(((-2.2, slope / 2), (slope / 2, slope + 0.4))):
            for j, (za, zb) in enumerate(((Z0 - 1.2, 16), (16, Z1 + 1.2))):
                e = bx(f"{nm}{k}{j}", (x - 0.25, EAVE + y1, za), (x + 0.25, EAVE + y2, zb), "fly", rot=(0, 0, sign * lean),
                       origin=(x, EAVE, 16))
                e["faces"]["east" if sign < 0 else "west"]["texture"] = "#inside"
                els.append(e)
    # The ridge pole and its cap of canvas, the uprights at front and back, the eave poles
    els += [bx("Ridge", (15.3, RIDGE - 1.2, Z0 - 1.4), (16.7, RIDGE + 0.1, Z1 + 1.4), "pole"),
            bx("RidgeCap", (14.6, RIDGE - 0.1, Z0 - 1.2), (17.4, RIDGE + 0.6, Z1 + 1.2), "fly"),
            bx("PoleF", (15.4, 0, Z0 + 0.6), (16.6, RIDGE - 1.2, Z0 + 1.8), "pole"),
            bx("PoleB", (15.4, 0, Z1 - 1.8), (16.6, RIDGE - 1.2, Z1 - 0.6), "pole"),
            bx("EaveL", (W0 - 0.2, EAVE - 0.8, Z0), (W0 + 0.8, EAVE, Z1), "pole"),
            bx("EaveR", (W1 - 0.8, EAVE - 0.8, Z0), (W1 + 0.2, EAVE, Z1), "pole")]

    # The ends: walls to the eave, then the gable stepped to the slope a pixel a step; the front has the door
    door_w, door_h = 4.6, 19.0

    def end(nm, z1, z2, front):
        out = []
        tex = "canvas"
        for (a, b) in ((W0, 16 - door_w), (16 + door_w, W1)) if front else ((W0, W1),):
            # (the panel left of the door carries the stencil)
            t = "stencil" if front and a == W0 else tex
            e = bx(f"{nm}Wall{a}", (a, 0, z1), (b, EAVE, z2), t, faces=("north", "south", "up", "east", "west"))
            if t == "stencil":
                e["faces"]["north"]["uv"] = [0, 0, round(b - a, 3), EAVE]
            e["faces"]["south" if front else "north"]["texture"] = "#inside"
            out.append(e)
        steps = 28
        for k in range(steps):
            y1, y2 = EAVE + rise * k / steps, EAVE + rise * (k + 1) / steps
            hw = (16 - W0) * (1 - (y2 - EAVE) / rise) + 0.2
            if hw <= 0.3:
                continue
            spans = [(16 - hw, 16 + hw)]
            if front and y2 <= door_h + 0.01:
                spans = [(16 - hw, 16 - door_w), (16 + door_w, 16 + hw)]
            for n, (a, b) in enumerate(spans):
                if b - a > 0.2:
                    e = bx(f"{nm}G{k}{n}", (a, y1, z1), (b, y2, z2), "canvas", faces=("north", "south", "up"))
                    e["faces"]["south" if front else "north"]["texture"] = "#inside"
                    out.append(e)
        return out

    els += end("Back", Z1 - 0.4, Z1, False)
    els += end("Front", Z0, Z0 + 0.4, True)
    # The door flaps tied back to each side of the doorway, bunched; a rolled valance over it
    for nm, x0, x1 in (("FlapL", 16 - door_w - 2.2, 16 - door_w + 0.3), ("FlapR", 16 + door_w - 0.3, 16 + door_w + 2.2)):
        els += [bx(nm, (x0, 0, Z0 - 1.0), (x1, door_h - 1, Z0 - 0.1), "canvas"),
                bx(nm + "Tie", (x0 - 0.1, 8, Z0 - 1.2), (x1 + 0.1, 9, Z0), "rope")]
    els += [bx("Valance", (16 - door_w, door_h - 1.5, Z0 - 1.1), (16 + door_w, door_h + 0.6, Z0), "canvas")]
    # Guy lines from each eave corner out to a peg, and pegs along the walls' feet
    for x, sx in ((W0, -1), (W1, 1)):
        for z in (Z0 + 2, 16, Z1 - 2):
            rope_len = math.hypot(3.5, EAVE)
            ang = math.degrees(math.atan2(3.5, EAVE))
            gx = x + sx * 3.5
            els.append(bx("Guy", (gx - 0.15, 0, z - 0.15), (gx + 0.15, rope_len, z + 0.15), "rope", rot=(0, 0, sx * ang), origin=(gx, 0, z)))
            # (turned a little, so the cut keeps it whole although it stands outside the tent's blocks)
            els.append(bx("Peg", (gx - 0.4, 0, z - 0.4), (gx + 0.4, 1.6, z + 0.4), "pole", rot=(0, 7, 0), origin=(gx, 0, z)))
    # The stovepipe through the fly at the back right, its rain cap and collar
    px, pz = 23.0, 25.0
    els += [bx("Pipe", (px - 0.9, 5, pz - 0.9), (px + 0.9, RIDGE + 5, pz + 0.9), "iron"),
            bx("PipeCap", (px - 1.8, RIDGE + 5, pz - 1.8), (px + 1.8, RIDGE + 5.6, pz + 1.8), "iron"),
            bx("PipeCapPost", (px - 0.3, RIDGE + 4.4, pz - 0.3), (px + 0.3, RIDGE + 5, pz + 0.3), "iron"),
            bx("Collar", (px - 1.6, 20.0, pz - 1.6), (px + 1.6, 21.2, pz + 1.6), "tin"),
            # The stove under it
            bx("Stove", (px - 3, 0.4, pz - 2.5), (px + 3, 5, pz + 2.5), "iron"),
            bx("StoveLegs", (px - 2.6, 0, pz - 2.1), (px + 2.6, 0.4, pz + 2.1), "iron"),
            bx("StoveDoor", (px - 1.5, 1.2, pz - 2.7), (px + 1.5, 3.8, pz - 2.5), "char")]
    # Inside: the groundsheet, a cot on the left (frame, legs, canvas, a folded blanket), a footlocker at its foot
    els += [bx("Floor", (W0 + 0.2, 0, Z0 + 0.4), (W1 - 0.2, 0.2, Z1 - 0.4), "floor", faces=("up",)),
            bx("CotBed", (3.5, 5.0, 6), (12.5, 5.8, 28), "bedcanvas"),
            bx("CotRailL", (3.2, 4.6, 6), (3.9, 5.6, 28), "pole"), bx("CotRailR", (12.1, 4.6, 6), (12.8, 5.6, 28), "pole")]
    for z in (6.5, 26.8):
        for x in (3.4, 11.8):
            els.append(bx("CotLeg", (x, 0, z), (x + 0.7, 4.6, z + 0.7), "pole"))
    els += [bx("CotBlanket", (3.8, 5.8, 18), (12.2, 7.0, 27.5), "blanket"),
            bx("CotPillow", (4.5, 5.8, 23.5), (11.5, 7.6, 27.4), "flannel"),
            bx("Locker", (4, 0.2, 2.6), (12, 5.2, 5.6), "board"),
            bx("LockerLid", (3.8, 5.2, 2.4), (12.2, 5.8, 5.8), "board"),
            bx("LockerHasp", (7.4, 3.6, 2.4), (8.6, 5.0, 2.6), "brass")]
    return els


# ---------------- Small things ----------------

def barrel():
    """Staves (an octagon in two crossed boxes and four chamfers), two iron hoops proud of them, the lid inset with its
    planks, a brass tap at the front, the WATER label flat on the front."""
    els = [bx("BodyX", (2.2, 0, 4), (13.8, 14.5, 12), "stave"), bx("BodyZ", (4, 0, 2.2), (12, 14.5, 13.8), "stave")]
    for k, (x, z) in enumerate(((3, 3), (11, 3), (3, 11), (11, 11))):
        els.append(bx(f"Chamfer{k}", (x, 0, z), (x + 2, 14.5, z + 2), "stave", rot=(0, 45, 0), origin=(x + 1, 0, z + 1)))
    for y in (2.2, 11.6):
        els += [bx("HoopX", (1.9, y, 3.8), (14.1, y + 1.1, 12.2), "iron", faces=("east", "west", "up", "down")),
                bx("HoopZ", (3.8, y, 1.9), (12.2, y + 1.1, 14.1), "iron", faces=("north", "south", "up", "down"))]
        for k, (x, z) in enumerate(((3, 3), (11, 3), (3, 11), (11, 11))):
            els.append(bx(f"HoopC{k}", (x - 0.3, y, z - 0.3), (x + 2.3, y + 1.1, z + 2.3), "iron", rot=(0, 45, 0), origin=(x + 1, y, z + 1),
                          faces=("north", "south", "east", "west", "up", "down")))
    els += [bx("Lid", (4.5, 14.0, 4.5), (11.5, 14.7, 11.5), "lid", faces=("up",)),
            bx("Bung", (9, 14.5, 6.5), (10.5, 15.1, 8), "lid"),
            bx("Label", (5, 4.2, 2.05), (11, 10.6, 2.2), "label", faces=("north",), over={"north": ("label", [2, 2, 14, 14])}),
            bx("TapBody", (7.2, 1.6, 1.0), (8.8, 2.8, 2.3), "brass"), bx("TapSpout", (7.6, 0.9, 0.6), (8.4, 1.8, 1.4), "brass"),
            bx("TapKey", (7.0, 2.8, 1.4), (9.0, 3.3, 1.8), "brass")]
    return els


def crate():
    """Boards round a body, battens on the edges, corner irons, a lid of boards a hair proud; M.E.G. on the front."""
    els = [bx("Body", (1, 0, 1), (15, 13.5, 15), "board", over={"north": ("front", [0, 1, 16, 15])})]
    for x in (0.6, 14.2):
        for z in (0.6, 14.2):
            els.append(bx("Batten", (x, 0, z), (x + 1.2, 13.5, z + 1.2), "board"))
            els.append(bx("Iron", (x - 0.1, 11.6, z - 0.1), (x + 1.3, 13.2, z + 1.3), "iron"))
            els.append(bx("IronLo", (x - 0.1, 0.4, z - 0.1), (x + 1.3, 2.0, z + 1.3), "iron"))
    els += [bx("BeltF", (1, 5.8, 0.7), (15, 7.2, 1), "board", faces=("north", "up", "down")),
            bx("BeltB", (1, 5.8, 15), (15, 7.2, 15.3), "board", faces=("south", "up", "down")),
            bx("Lid", (0.5, 13.5, 0.5), (15.5, 14.8, 15.5), "board"),
            bx("LidSlot", (4, 14.8, 7.6), (12, 14.9, 8.4), "char", faces=("up",))]
    return els


def campfire():
    """Stones round a bed of ash, charred logs crossed in it, embers glowing, a tripod of poles with a pot hung from it."""
    els, rng = [], random.Random(23)
    for k in range(9):
        a = k * math.pi * 2 / 9 + rng.uniform(-0.1, 0.1)
        x, z = 8 + math.cos(a) * 6.3, 8 + math.sin(a) * 6.3
        w, h = rng.uniform(2.4, 3.2), rng.uniform(1.8, 2.8)
        els += [bx(f"Stone{k}", (x - w / 2, 0, z - w / 2), (x + w / 2, h, z + w / 2), "stone", rot=(0, math.degrees(-a) + rng.uniform(-15, 15), 0),
                   origin=(x, 0, z)),
                bx(f"StoneTop{k}", (x - w / 2 + 0.5, h, z - w / 2 + 0.5), (x + w / 2 - 0.5, h + 0.6, z + w / 2 - 0.5), "stone",
                   rot=(0, math.degrees(-a), 0), origin=(x, 0, z))]
    els += [bx("Ash", (2.8, 0, 2.8), (13.2, 0.5, 13.2), "ash", faces=("up",)),
            bx("Embers", (5, 0.3, 5), (11, 0.9, 11), "ember", glow=200)]
    for k, ang in enumerate((25, 85, 145)):
        els.append(bx(f"Log{k}", (3.5, 0.8, 7.2), (12.5, 2.4, 8.8), "char", rot=(0, ang, 8 if k % 2 else -6), origin=(8, 1.6, 8)))
    els += [bx("Flame", (6.8, 1.2, 6.8), (9.2, 4.2, 9.2), "flame", glow=255, rot=(0, 45, 0), origin=(8, 1.2, 8)),
            bx("Flame2", (7.2, 1.2, 7.2), (8.8, 5.6, 8.8), "flame", glow=255)]
    # The tripod: three poles from the ground at the ring's edge to the apex over the middle
    apex = 19.0
    for k in range(3):
        a = k * math.pi * 2 / 3 + 0.4
        fx, fz = 8 + math.cos(a) * 7.5, 8 + math.sin(a) * 7.5
        dx, dz = 8 - fx, 8 - fz
        length = math.sqrt(dx * dx + dz * dz + apex * apex)
        tilt = math.degrees(math.atan2(math.hypot(dx, dz), apex))
        ux, uz = dx / math.hypot(dx, dz), dz / math.hypot(dx, dz)
        # A pole up y from its foot, leaning toward the middle: the game turns a point by z, then y, then x (check_zfight.py's
        # order), so z tilts +y toward -x by the lean and y then swings that to the bearing
        yaw = math.degrees(math.atan2(uz, -ux))
        els.append(bx(f"Leg{k}", (fx - 0.4, 0, fz - 0.4), (fx + 0.4, length, fz + 0.4), "pole", rot=(0, yaw, tilt), origin=(fx, 0, fz)))
    els += [bx("Lashing", (7.3, apex - 1.5, 7.3), (8.7, apex, 8.7), "rope"),
            bx("Chain", (7.85, 9.6, 7.85), (8.15, apex - 1.4, 8.15), "iron"),
            bx("Pot", (5.6, 5.4, 5.6), (10.4, 9.0, 10.4), "iron"), bx("PotRim", (5.3, 8.6, 5.3), (10.7, 9.2, 10.7), "iron"),
            bx("Bail", (5.4, 9.2, 7.85), (10.6, 9.6, 8.15), "iron")]
    return els


def campbed():
    """A bedroll laid out, head north: the mat, a quilted sleeping bag turned back at the head over its flannel lining, a
    pillow, a strapped roll at the foot."""
    return [bx("Mat", (2, 0, 0.5), (14, 0.6, 15.8), "bedcanvas"),
            bx("Bag", (3, 0.6, 3.5), (13, 2.2, 15.4), "quilt"),
            bx("Turned", (3, 2.2, 3.5), (13, 2.7, 7.5), "flannel"),
            bx("Fold", (2.9, 2.2, 7.4), (13.1, 3.2, 8.6), "quilt"),
            bx("Pillow", (4, 0.6, 0.8), (12, 3.2, 3.6), "flannel"),
            bx("Roll", (3.5, 0.6, 13.2), (12.5, 3.6, 15.8), "blanket"),
            bx("Strap1", (5, 0.55, 13.0), (5.8, 3.8, 16), "pole"), bx("Strap2", (10.2, 0.55, 13.0), (11, 3.8, 16), "pole")]


def camplamp():
    """A hurricane lantern: the fount, a wire guard round the globe, the globe glowing, the chimney and its cap, the bail."""
    els = [bx("Fount", (4.8, 0, 4.8), (11.2, 2.6, 11.2), "tin"), bx("FountTop", (5.6, 2.6, 5.6), (10.4, 3.2, 10.4), "tin"),
           bx("Globe", (5.6, 3.2, 5.6), (10.4, 8.6, 10.4), "globe", glow=255),
           bx("GlobeMid", (5.1, 4.4, 5.1), (10.9, 7.4, 10.9), "globe", glow=255),
           bx("Collar", (5.6, 8.6, 5.6), (10.4, 9.4, 10.4), "tin"), bx("Chimney", (6.5, 9.4, 6.5), (9.5, 11.2, 9.5), "tin"),
           bx("Cap", (6.0, 11.2, 6.0), (10.0, 11.8, 10.0), "tin")]
    for k, (x, z) in enumerate(((4.6, 7.7), (11.0, 7.7), (7.7, 4.6), (7.7, 11.0))):
        els.append(bx(f"Wire{k}", (x, 3.0, z), (x + 0.4, 9.0, z + 0.4), "iron"))
    els += [bx("Bail", (4.4, 11.6, 7.8), (11.6, 12.1, 8.2), "iron"),
            bx("BailL", (4.4, 9.0, 7.8), (4.9, 12.1, 8.2), "iron"), bx("BailR", (11.1, 9.0, 7.8), (11.6, 12.1, 8.2), "iron"),
            bx("Key", (10.9, 1.2, 7.6), (12.0, 2.0, 8.4), "brass")]
    return els


def counter():
    """The quartermaster's counter, three blocks wide, front north: a plank top overhanging, the front boarded with
    battens, posts, a shelf under with tins (seen from behind), a balance and a cash tin on top at the right end."""
    els = [bx("Top", (0, 14.6, 0), (48, 16, 15), "plank"),
           bx("Front", (0.5, 0, 1), (47.5, 14.6, 2), "plank", faces=("north", "south", "east", "west")),
           bx("Shelf", (0.5, 5, 2), (47.5, 5.8, 14), "plank"),
           bx("Kick", (0.5, 0, 0.6), (47.5, 1.2, 1), "plank")]
    for x in (0.3, 15.6, 31.6, 46.6):
        els += [bx("Post", (x, 0, 0.4), (x + 1.1, 14.6, 1.6), "pole"), bx("PostB", (x, 0, 13.4), (x + 1.1, 14.6, 14.6), "pole")]
    for k, x in enumerate((3, 8, 19, 25, 35, 40)):
        els.append(bx(f"Tin{k}", (x, 5.8, 8), (x + 3.4, 10.2, 11.4), "tins"))
    # The balance: base, column, beam, two pans
    els += [bx("ScaleBase", (37, 16, 5), (43, 16.6, 10), "brass"), bx("ScaleCol", (39.6, 16.6, 7.1), (40.4, 22, 7.9), "brass"),
            bx("ScaleBeam", (36, 21.6, 7.2), (44, 22.2, 7.8), "brass"),
            bx("PanL", (35.2, 18.6, 5.6), (38.8, 19.0, 9.4), "brass"), bx("PanR", (41.2, 18.6, 5.6), (44.8, 19.0, 9.4), "brass"),
            bx("CordL", (36.9, 19, 7.3), (37.1, 21.6, 7.7), "rope"), bx("CordR", (42.9, 19, 7.3), (43.1, 21.6, 7.7), "rope"),
            # A cash tin and a pencil at the left end
            bx("CashTin", (4, 16, 4), (10, 18.2, 9), "tins"), bx("Pencil", (12, 16, 6), (16.5, 16.5, 6.5), "brass")]
    return els


# ---------------- Blocktypes ----------------

def sided(code, comment, shp_of_part, parts, material, sounds, drops=(), boxes=None, extra=None, partnered=False):
    shape_by = {}
    groups = []
    if parts:
        groups.append({"code": "part", "states": parts})
        for p in parts:
            for s in SIDES:
                shape_by[f"*-{p}-{s}"] = {"base": f"block/23/{shp_of_part(p)}", "rotateY": ROT[s]}
    else:
        for s in SIDES:
            shape_by[f"*-{s}"] = {"base": f"block/23/{shp_of_part(None)}", "rotateY": ROT[s]}
    groups.append({"code": "side", "states": SIDES})
    first = f"*-{parts[0]}-north" if parts else "*-north"
    b = {"code": code, "variantgroups": groups, "creativeinventory": {"general": [first], "backrooms": [first]},
         "blockmaterial": material, "drawtype": "json", "shapeByType": shape_by,
         "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 1.5,
         "drops": list(drops), "sounds": sounds}
    if partnered:
        b["behaviors"] = [{"name": "BackroomsPartnered", "properties": {"parts": parts, "width": partnered}}]
    if boxes:
        keyed = {}
        for p in (parts or [None]):
            bxx = boxes(p)
            for s in SIDES:
                k = f"*-{p}-{s}" if p else f"*-{s}"
                keyed[k] = dict(bxx, rotateY=ROT[s]) if bxx else None
        b["collisionboxByType"] = keyed
        b["selectionboxByType"] = {k: v for k, v in keyed.items() if v}
    if extra:
        b.update(extra)
    return comment, b


def plain(code, comment, shp, material, sounds, drops=(), box=None, extra=None):
    b = {"code": code, "creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": material, "drawtype": "json",
         "shape": {"base": f"block/23/{shp}"}, "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0,
         "resistance": 1.5, "drops": list(drops), "sounds": sounds}
    if box is not None:
        b["collisionbox"] = box
        b["selectionbox"] = box
    if extra:
        b.update(extra)
    return comment, b


def blocks():
    out = []
    tent_boxes = {"nw": {"x1": 0.1, "y1": 0, "z1": 0.05, "x2": 1, "y2": 1.5, "z2": 1}, "ne": {"x1": 0, "y1": 0, "z1": 0.05, "x2": 0.9, "y2": 1.5, "z2": 1},
                  "sw": {"x1": 0.1, "y1": 0, "z1": 0, "x2": 1, "y2": 1.5, "z2": 0.95}, "se": {"x1": 0, "y1": 0, "z1": 0, "x2": 0.9, "y2": 1.5, "z2": 0.95}}
    out.append(sided("l23-tent", "// Level 23 (round 4): the M.E.G.'s canvas wall tent at Base Seedling, two blocks by two, its door to the north (nw, ne the front; sw, se the back); similar to the detail kit's camptent",
                     lambda p: f"tent-{p}", ["nw", "ne", "sw", "se"], "Cloth", CLOTH, boxes=lambda p: tent_boxes[p], partnered=2))
    out.append(plain("l23-campbarrel", "// Level 23 (round 4): Base Seedling's water barrel (only looks: drink at the spring)", "campbarrel", "Wood", WOODS,
                     drops=[G.drop("game:plank-oak", 2, 1)], box={"x1": 0.12, "y1": 0, "z1": 0.12, "x2": 0.88, "y2": 0.92, "z2": 0.88}))
    out.append(plain("l23-campcrate", "// Level 23 (round 4): an M.E.G. crate (boards, battens, corner irons, a lid)", "campcrate", "Wood", WOODS,
                     drops=[G.drop("game:plank-oak", 2, 1)], box={"x1": 0.03, "y1": 0, "z1": 0.03, "x2": 0.97, "y2": 0.93, "z2": 0.97}))
    out.append(plain("l23-campfire", "// Level 23 (round 4): Base Seedling's fire: a ring of stones, logs and embers, a tripod and a pot (gives light, drops nothing)",
                     "campfire", "Stone", STONES, box={"x1": 0.05, "y1": 0, "z1": 0.05, "x2": 0.95, "y2": 0.25, "z2": 0.95},
                     extra={"lightHsv": [7, 7, 11]}))
    out.append(sided("l23-campbed", "// Level 23 (round 4): a bedroll by the tents at Base Seedling (only looks)", lambda p: "campbed", None, "Cloth", CLOTH,
                     boxes=lambda p: {"x1": 0.12, "y1": 0, "z1": 0, "x2": 0.88, "y2": 0.2, "z2": 1}))
    out[-1][1].pop("collisionboxByType")
    out[-1][1]["collisionbox"] = None
    out.append(plain("l23-camplamp", "// Level 23 (round 4): the M.E.G.'s hurricane lantern (bolted down; breaks to nothing)", "camplamp", "Metal",
                     {"walk": "game:walk/stone*", "place": "game:block/anvil", "break": "game:block/glass", "hit": "game:block/anvil"},
                     box={"x1": 0.28, "y1": 0, "z1": 0.28, "x2": 0.72, "y2": 0.75, "z2": 0.72}, extra={"lightHsv": [7, 4, 14]}))
    out.append(sided("l23-counter", "// Level 23 (round 4): the quartermaster's counter at Base Seedling, three blocks (l, m, r from the west, front north)",
                     lambda p: f"counter-{p}", ["l", "m", "r"], "Wood", WOODS, drops=[G.drop("game:plank-oak", 2, 1)],
                     boxes=lambda p: {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 1, "z2": 0.95}))
    return out


def shapes():
    out = {}
    cut = split(wall_tent(), 2, 2)
    for n, part in enumerate(["nw", "ne", "sw", "se"]):
        out[f"tent-{part}"] = shape(TEX, cut[(n % 2, n // 2)])
    cut = split(counter(), 3, 1)
    for n, part in enumerate(["l", "m", "r"]):
        out[f"counter-{part}"] = shape(TEX, cut[(n, 0)])
    out["campbarrel"] = shape(TEX, barrel())
    out["campcrate"] = shape(TEX, crate())
    out["campfire"] = shape(TEX, campfire())
    out["campbed"] = shape(TEX, campbed())
    out["camplamp"] = shape(TEX, camplamp())
    return out


LANG = [
    ("block-l23-tent-*", "M.E.G. Wall Tent"),
    ("blockdesc-l23-tent-*", "Canvas on poles, a stovepipe through the roof, M.E.G. 23-1 stencilled by the door. Somebody sleeps here; leave it be."),
    ("block-l23-campbarrel", "Water Barrel"),
    ("blockdesc-l23-campbarrel", "Stencilled DRINKING WATER. The spring fills them; the M.E.G. say drink from the spring itself."),
    ("block-l23-campcrate", "M.E.G. Crate"),
    ("block-l23-campfire", "Camp Fire"),
    ("blockdesc-l23-campfire", "Petrified wood does not burn. Nobody at Seedling will say what they feed it with."),
    ("block-l23-campbed-*", "Bedroll"),
    ("block-l23-camplamp", "M.E.G. Lantern"),
    ("blockdesc-l23-camplamp", "Bolted down and wired shut. The M.E.G. keep the ways to Seedling lit, and they count their lanterns."),
    ("block-l23-counter-*", "Quartermaster's Counter"),
    ("blockdesc-l23-counter-*", "Rations by the book, water for free. The balance is for trading; the quartermaster's thumb is not on it, he says."),
]
