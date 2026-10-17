"""Level 3999, graphics pass B16: the painters and model parts that replace B0's flat ones. Called from gen_3999_tex.generate
(textures, after the old painters, under the same keys plus new version keys) and from gen_3999_blocks / gen_3999_arcade
(models). Each family has its own function, so dropping its call reverts it to the old look:

- `marble`: the white and black marble floors (and the lobby's black storey line) as polished 2 x 2 tiles whose veins
  are cut from one large slab, every tile a different piece, four versions of a block on one tone; B0 drew one vein
  scribble and a diagonal gloss band that repeated on every block.
- `paint`: the violet, midnight and teal painted plaster (shopfront fascias, gallery walls) in three versions.
- `furniture_textures`, `chair`, `table`, `booth`: the food court's moulded plastic chairs, round pedestal tables and
  diner booths as modelled pieces (shell seat and back with a rolled lip, tube legs with glides, a table top with an
  edge band, a pedestal collar and a four-star foot; the booth's back in buttoned channels on a chrome plinth).
- `cabinet_textures`, `cabinet_parts`: the arcade cabinet's coin door as an inset with slots and coin buttons, a rim
  round the screen bezel, the marquee in a frame, the control panel's front bumper; laminate on the body.
- `vending_textures`, `vending_parts`: shelves and product boxes behind the vending machines' glass.

The neon (tubes, signs, pillars, base strips) and every light and glow are unchanged.
"""
import math
import random

import numpy as np
from PIL import Image

import matlib as M
from gen_3999_tex import save, seed_of, clamp

S = 32
# How many versions each B16 surface has (the first is the key itself, the rest key-2, key-3...). The block types read
# this whether or not the textures are painted in the same run; drop a family's entry with its painter to revert it.
COUNTS = {"marble-white": 4, "marble-black": 4, "wall-violet": 3, "wall-midnight": 3, "wall-teal": 3}


def register(key, n=None):
    return versions(key)


def versions(key):
    """The texture keys of a surface's versions (only the key itself for a surface B16 does not version)."""
    return [key] + [f"{key}-{i}" for i in range(2, COUNTS.get(key, 1) + 1)]


def img_of(a):
    a = np.clip(np.rint(a), 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([a, np.full(a.shape[:2], 255, np.uint8)]), "RGBA")


def arr(img):
    return np.asarray(img.convert("RGBA"), dtype=np.float64)[:, :, :3].copy()


def mean_rgb(img):
    return arr(img).reshape(-1, 3).mean(axis=0)


def match(a, target, amount=1.0):
    """a (H x W x 3) shifted so its mean is target's (each channel), by `amount`."""
    return a + (np.asarray(target) - a.reshape(-1, 3).mean(axis=0)) * amount


# ---------------------------------------------------------------- fields (numpy, not tileable: the joints hide edges)

def vnoise(n, cell, rng):
    g = rng.uniform(-1, 1, (n // cell + 2, n // cell + 2))
    y, x = np.mgrid[0:n, 0:n] / cell
    i, j = x.astype(int), y.astype(int)
    tx, ty = x - i, y - j
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    a = g[j, i] * (1 - tx) + g[j, i + 1] * tx
    b = g[j + 1, i] * (1 - tx) + g[j + 1, i + 1] * tx
    return a * (1 - ty) + b * ty


def fbm(n, rng, cells=(64, 32, 16, 8), gain=0.55):
    acc, amp = np.zeros((n, n)), 1.0
    for c in cells:
        acc += amp * vnoise(n, c, rng)
        amp *= gain
    return acc / np.abs(acc).max()


# ---------------------------------------------------------------- marble

MARBLE = {
    # key: base, primary vein, secondary (cloud) vein, joint, old look's means kept
    "marble-white": ((233, 230, 238), (146, 142, 158), (198, 194, 208), (196, 192, 202)),
    "marble-black": ((22, 18, 26), (214, 190, 130), (58, 50, 56), (44, 38, 46)),
}


def marble_slab(key, n=384):
    """One large slab of veined marble: a soft cloud, a network of fine primary veins that wander (a sine across the
    slab, bent by turbulence), finer branch veins, and fainter broad secondary veins at another angle. Not tileable:
    tiles are cut from it."""
    base, vein, cloud, _ = MARBLE[key]
    rng = np.random.default_rng(seed_of(key + "slab"))
    y, x = np.mgrid[0:n, 0:n].astype(np.float64)
    turb = fbm(n, rng, (96, 48, 24, 12, 6))
    turb2 = fbm(n, rng, (64, 32, 16, 8))
    turb3 = fbm(n, rng, (32, 16, 8, 4))
    mott = fbm(n, rng, (48, 24, 12))
    th1, th2, th3 = (math.radians(rng.uniform(25, 40)), math.radians(rng.uniform(-70, -50)), math.radians(rng.uniform(-10, 10)))
    w1 = np.sin(2 * math.pi * (x * math.cos(th1) + y * math.sin(th1)) / 38 + 6.5 * turb)
    w2 = np.sin(2 * math.pi * (x * math.cos(th2) + y * math.sin(th2)) / 30 + 4.0 * turb2)
    w3 = np.sin(2 * math.pi * (x * math.cos(th3) + y * math.sin(th3)) / 17 + 5.0 * turb3)
    dark = key == "marble-black"
    p = np.exp(-(8.0 if dark else 7.0) * np.abs(w1))           # fine primary veins
    p *= 0.55 + 0.45 * np.clip(fbm(n, rng, (64, 32)) + 0.4, 0, 1)  # veins fade in and out along their length
    br = np.exp(-8.0 * np.abs(w3)) * np.clip(fbm(n, rng, (64, 32)) + 0.5, 0, 1) * (0.0 if dark else 0.32)  # faint branches (none on the black: they read as dashes)
    s = np.exp(-2.6 * np.abs(w2)) * (0.30 if dark else 0.45)  # broad, faint secondary veins (cloudy drifts)
    out = np.empty((n, n, 3))
    v_all = np.clip(np.maximum(p * (0.9 if dark else 0.78), br), 0, 1)
    for c in range(3):
        v = base[c] + (cloud[c] - base[c]) * s
        v = v + (vein[c] - v) * v_all
        out[:, :, c] = v + mott * (5 if not dark else 3)
    return out


def marble(key, n=4, joint_strength=1.0):
    """n versions of a 2 x 2 marble tile block: each 15 px tile a different piece of one slab, turned at random, its
    mean evened toward the stone's (so the floor is not a plaid), a 1 px joint at the top and left of each tile (the
    neighbour's tile closes the other side), a faint lit top edge and shaded foot on each tile (polished, flat)."""
    base, vein, cloud, joint = MARBLE[key]
    old = mean_rgb(Image.open(_old_path(key)))
    slab = marble_slab(key)
    rng = random.Random(seed_of(key + "cut"))
    N = slab.shape[0]
    keys = versions(key)
    grain = np.random.default_rng(seed_of(key + "grain"))
    dark = key == "marble-black"
    stone_mean = None
    tiles_all = []
    for v in range(n):
        tiles = []
        for t in range(4):
            x0, y0 = rng.randrange(0, N - 16), rng.randrange(0, N - 16)
            tile = slab[y0:y0 + 15, x0:x0 + 15].copy()
            tile = np.rot90(tile, rng.randrange(4))
            tiles.append(tile)
        tiles_all.append(tiles)
    stone_mean = np.mean([t.reshape(-1, 3).mean(axis=0) for ts in tiles_all for t in ts], axis=0)
    for v, k in enumerate(keys):
        a = np.empty((S, S, 3))
        for c in range(3):
            a[:, :, c] = joint[c]
        for t, tile in enumerate(tiles_all[v]):
            tx, ty = (t % 2) * 16, (t // 2) * 16
            tile = tile + (stone_mean - tile.reshape(-1, 3).mean(axis=0)) * 0.75   # tone evened, veins kept
            tile = tile + rng.uniform(-1.5, 1.5)                                      # each tile a touch apart
            tile[0, :, :] += 3.0 if not dark else 4.0       # the lit top edge of a polished tile
            tile[:, 0, :] += 1.5 if not dark else 2.0
            tile[-1, :, :] -= 3.0 if not dark else 2.0      # its foot, toward the joint below
            a[ty + 1:ty + 16, tx + 1:tx + 16] = tile
        # the joint: recessed grout, darker under the tile above it
        jn = grain.uniform(-1.5, 1.5, (S, S))
        for r in (0, 16):
            a[r, :, :] = np.asarray(joint) + jn[r, :, None] - 2 * joint_strength
        for col in (0, 16):
            a[:, col, :] = np.asarray(joint) + jn[:, col, None]
        a += grain.uniform(-1.2, 1.2, (S, S, 1))
        a = match(a, old, 0.35 if dark else 1.0)  # black stays black (B0's mean was lifted by its heavy gold)
        save(img_of(a), k)
    return keys


def _old_path(key):
    import os
    from gen_3999_tex import TEX
    return os.path.join(TEX, "block", "3999", key + ".png")


# ---------------------------------------------------------------- painted plaster (fascias, gallery walls)

PAINTS = ("wall-violet", "wall-midnight", "wall-teal")


def paint(n=3):
    """Matt paint over plaster in the old colours: one calm broad ground shared by every version (turn_safe keeps any
    two versions meeting), each version its own fine roller stipple and a few filled bumps; means kept."""
    for key in PAINTS:
        old = Image.open(_old_path(key))
        om = mean_rgb(old)
        keys = versions(key)
        ground = M.noise_hv(tuple(om), 0, sub_seed(key, "ground"), S, mottle=3, cells=(32, 16), hue=1.0)
        for i, k in enumerate(keys):
            img = M.plaster(seed=sub_seed(key, f"v{i}"), base=tuple(om), grain=2, mottle=3, roller=0.35, bumps=0.006)
            img = M.turn_safe(img, ground, band=8, radius=3, keep=0.6)
            a = match(arr(img), om)
            save(img_of(a), k)


def sub_seed(key, tag):
    return M.sub(seed_of(key), tag)


# ---------------------------------------------------------------- food court furniture

PLASTIC = {"white": (236, 236, 232), "pink": (255, 120, 170), "cyan": (90, 220, 230)}


def gloss(c, seed, side=False, sheen=(9, 7), amp=1.5):
    """Moulded plastic: the colour, a broad soft sheen up and to the left (the top of a seat catches the light), a very
    fine grain; a side face is a step darker and has no sheen."""
    base = M.lift(c, -14) if side else c
    img = M.noise_hv(base, amp, seed, S, mottle=2, cells=(16, 8), hue=0.8)
    px = img.load()
    if not side:
        for y in range(S):
            for x in range(S):
                t = math.exp(-(((x - sheen[0]) / 14.0) ** 2 + ((y - sheen[1]) / 10.0) ** 2))
                px[x, y] = M.rgba(M.lift(px[x, y], 5 * t), 255)
    return img


def furniture_textures():
    for name, c in PLASTIC.items():
        save(gloss(c, seed_of("plastic" + name)), f"plastic-{name}")
        save(gloss(c, seed_of("plasticside" + name), side=True), f"plastic-{name}-side")
    # The table: a white laminate top (a faint sheen), its aluminium edge band, a satin chrome pedestal, rubber glides
    # no sheen on the top: it is drawn by four crossed boxes, whose faces map the texture each its own way
    save(M.noise_hv((244, 242, 248), 1.2, seed_of("fc-top"), S, mottle=1, hue=0.5), "fc-top")
    save(M.brushed_metal(seed=seed_of("fc-edge"), base=(176, 178, 186), streak=6, sheen=8), "fc-edge")
    save(M.brushed_metal(seed=seed_of("fc-chrome"), base=(196, 200, 208), direction="v", streak=7, sheen=14), "fc-chrome")
    save(M.rubber(seed=seed_of("fc-glide"), base=(40, 38, 42)), "fc-glide")
    # The booth: pink vinyl (no painted channels: the back's channels are geometry now), a darker piping and side
    vinyl = (240, 110, 160)
    save(gloss(vinyl, seed_of("vinyl-pink"), sheen=(16, 8), amp=2.0), "vinyl-pink")
    save(gloss(vinyl, seed_of("vinyl-pink-side"), side=True, amp=2.0), "vinyl-pink-side")
    img = M.noise_hv(M.lift(vinyl, -34), 2, seed_of("vinyl-piping"), S, mottle=2)
    save(img, "vinyl-piping")
    save(M.brushed_metal(seed=seed_of("fc-kick"), base=(150, 152, 160), streak=6, sheen=6), "fc-kick")


def mbox(name, frm, to, tex, faces=None, rot=None, origin=None):
    import modelkit as MK
    return MK.box(name, frm, to, tex, faces=faces or MK.DIRS, rot=rot, origin=origin)


def octagon(name, cx, cz, r, y1, y2, tex, step=0.02, faces=None):
    """A regular octagon of inradius r: two crossed boxes and the same turned 45 degrees (their union is exactly the
    octagon). Each box's top and bottom are moved a hair apart, so no two faces share a plane (no shimmer)."""
    a = r * math.tan(math.pi / 8)
    els = []
    for k, (hx, hz, ry) in enumerate(((r, a, 0), (a, r, 0), (r, a, 45), (a, r, 45))):
        d = k * step
        els.append(mbox(f"{name}{k}", (cx - hx, y1 + d, cz - hz), (cx + hx, y2 - d, cz + hz), tex, faces=faces,
                        rot=(0, ry, 0) if ry else None, origin=(cx, y1, cz)))
    return els


def chair(colour):
    """A one-piece moulded shell chair facing north: a dished seat with a rolled front lip and raised side edges, a back
    shell leaning back with a rolled top, joined to the seat by a spine; four chrome tube legs on rubber glides, side
    rails under the seat and a stretcher between the front legs."""
    top, side = f"plastic-{colour}", f"plastic-{colour}-side"
    shell = {"top": top, "front": top, "side": side, "back": side, "bottom": side}
    els = []
    # legs and frame
    for i, (x, z) in enumerate(((3.6, 3.6), (12.4, 3.6), (3.6, 11.6), (12.4, 11.6))):
        els.append(mbox(f"Leg{i}", (x - 0.5, 0.5, z - 0.5), (x + 0.5, 6.6, z + 0.5), "fc-chrome"))
        els.append(mbox(f"Glide{i}", (x - 0.65, 0, z - 0.65), (x + 0.65, 0.5, z + 0.65), "fc-glide"))
    els.append(mbox("RailW", (3.25, 5.8, 4.0), (3.95, 6.5, 11.2), "fc-chrome", faces=("east", "west", "up", "down")))
    els.append(mbox("RailE", (12.05, 5.8, 4.0), (12.75, 6.5, 11.2), "fc-chrome", faces=("east", "west", "up", "down")))
    els.append(mbox("Stretcher", (4.0, 2.2, 3.3), (12.0, 2.8, 3.9), "fc-chrome", faces=("north", "south", "up", "down")))
    # the seat: a plate, raised side edges (the dish), a rolled front lip
    els.append(mbox("Seat", (2.8, 6.6, 3.0), (13.2, 7.4, 12.4), shell))
    els.append(mbox("SeatEdgeW", (2.8, 7.4, 3.6), (3.7, 7.9, 12.2), shell, faces=("north", "east", "west", "up", "south")))
    els.append(mbox("SeatEdgeE", (12.3, 7.4, 3.6), (13.2, 7.9, 12.2), shell, faces=("north", "east", "west", "up", "south")))
    els.append(mbox("Lip", (3.0, 6.2, 2.2), (13.0, 7.7, 3.0), shell))
    els.append(mbox("LipUnder", (3.4, 5.9, 2.5), (12.6, 6.2, 3.0), side, faces=("north", "down", "east", "west")))
    # the spine: where the seat turns up into the back
    els.append(mbox("Spine", (3.1, 7.4, 11.6), (12.9, 9.2, 12.8), shell, faces=("north", "south", "east", "west", "up")))
    # the back shell, leaning back 8 degrees about the spine
    o = (8, 8.6, 12.4)
    back = [mbox("Back", (3.0, 8.8, 12.0), (13.0, 16.2, 12.9), {"front": top, "back": side, "side": side, "top": side, "bottom": side}),
            mbox("BackRoll", (2.8, 15.8, 11.6), (13.2, 17.0, 13.1), shell),
            mbox("BackEdgeW", (3.0, 9.4, 11.5), (3.8, 15.8, 12.0), shell, faces=("north", "east", "west")),
            mbox("BackEdgeE", (12.2, 9.4, 11.5), (13.0, 15.8, 12.0), shell, faces=("north", "east", "west"))]
    for el in back:
        el["rotationOrigin"] = list(o)
        el["rotationX"] = -8
    return els + back


def table():
    """The round pedestal table: a laminate top 12 across with an aluminium edge band set under it, a spider of two bars
    under the top, a chrome column with a collar, and a four-star foot on rubber glides round a hub."""
    els = octagon("Top", 8, 8, 6.0, 11.2, 12.0, {"top": "fc-top", "bottom": "fc-edge", "side": "fc-edge"})
    els += octagon("Band", 8, 8, 5.85, 10.5, 11.2, "fc-edge", faces=("north", "east", "south", "west", "down"))
    els += [mbox("SpiderA", (4.0, 9.9, 7.5), (12.0, 10.5, 8.5), "fc-chrome", faces=("north", "south", "east", "west", "down")),
            mbox("SpiderB", (7.5, 9.9, 4.0), (8.5, 10.5, 12.0), "fc-chrome", faces=("north", "south", "east", "west", "down"))]
    els += octagon("Collar", 8, 8, 1.35, 8.6, 9.9, "fc-chrome")
    els += octagon("Column", 8, 8, 0.85, 1.4, 8.6, "fc-chrome", faces=("north", "east", "south", "west"))
    els += octagon("Hub", 8, 8, 1.5, 0.4, 1.6, "fc-chrome")
    els += [mbox("FootA", (2.6, 0.5, 7.4), (13.4, 1.1, 8.6), "fc-chrome", faces=("north", "south", "east", "west", "up")),
            mbox("FootB", (7.4, 0.5, 2.6), (8.6, 1.1, 13.4), "fc-chrome", faces=("north", "south", "east", "west", "up"))]
    for i, (x, z) in enumerate(((3.2, 8), (12.8, 8), (8, 3.2), (8, 12.8))):
        els.append(mbox(f"Glide{i}", (x - 0.7, 0, z - 0.7), (x + 0.7, 0.5, z + 0.7), "fc-glide"))
    return els


def booth():
    """A diner booth seat facing north: a chrome kick strip, a pink vinyl base, a seat cushion with a rolled front and
    a darker piping, the back in three buttoned channels standing proud of its panel, a chrome cap."""
    seat = {"top": "vinyl-pink", "front": "vinyl-pink", "side": "vinyl-pink-side", "back": "vinyl-pink-side", "bottom": "vinyl-pink-side"}
    els = [mbox("Kick", (0, 0, 3.4), (16, 1.0, 15), "fc-kick", faces=("north", "up", "east", "west")),
           mbox("Base", (0, 1.0, 3.0), (16, 6.0, 15), {"front": "vinyl-pink-side", "side": "vinyl-pink-side", "top": "vinyl-pink-side",
                                                         "back": "vinyl-pink-side", "bottom": "vinyl-pink-side"},
                faces=("north", "east", "west", "south", "up")),
           mbox("Edge", (0, 5.5, 2.0), (16, 6.3, 3.0), "fc-kick", faces=("north", "up", "down", "east", "west")),
           mbox("Seat", (0, 6.3, 2.4), (16, 8.8, 13.0), seat),
           mbox("SeatRoll", (0, 6.6, 1.7), (16, 8.5, 2.4), seat, faces=("north", "up", "down", "east", "west")),
           mbox("Piping", (0, 8.8, 2.2), (16, 9.2, 2.8), "vinyl-piping", faces=("north", "up", "east", "west")),
           mbox("BackPanel", (0, 6.0, 14.0), (16, 22.0, 16.0), {"front": "vinyl-pink-side", "side": "vinyl-pink-side", "back": "vinyl-pink-side",
                                                               "top": "vinyl-pink-side", "bottom": "vinyl-pink-side"}),
           mbox("BackCap", (0, 22.0, 12.4), (16, 23.0, 16.0), "fc-kick")]
    back = {"front": "vinyl-pink", "top": "vinyl-pink", "side": "vinyl-pink-side", "back": "vinyl-pink-side", "bottom": "vinyl-pink-side"}
    for i, (x1, x2) in enumerate(((0.3, 5.1), (5.6, 10.4), (10.9, 15.7))):
        els.append(mbox(f"Channel{i}", (x1, 9.0, 12.8), (x2, 21.2, 14.0), back, faces=("north", "east", "west", "up")))
        els.append(mbox(f"ChannelTop{i}", (x1 + 0.4, 21.2, 13.0), (x2 - 0.4, 21.7, 14.0), back, faces=("north", "east", "west", "up")))
        cx = (x1 + x2) / 2
        for j, y in enumerate((12.0, 17.0)):
            els.append(mbox(f"Button{i}{j}", (cx - 0.35, y, 12.55), (cx + 0.35, y + 0.7, 12.8), "vinyl-piping", faces=("north", "east", "west", "up", "down")))
    return els


# ---------------------------------------------------------------- arcade cabinets

def cabinet_textures():
    """The coin door as a plate (its slots and buttons are geometry now; ONE CREDIT stays in pixel type), the coin
    mechanism's chrome, the red coin buttons, the panel's rubber bumper, the bezel and marquee trim, and the cabinets'
    body paint as painted wood with a faint orange peel and a few worn spots (B0: one flat noise colour)."""
    from PIL import ImageDraw
    from gen_3999_kit import F3, draw_text
    from gen_3999_tex_arcade import GAMES
    img = M.painted_metal(seed=seed_of("coindoor-plate"), base=(62, 62, 68), panel=True, chips=2, screws=True)
    draw_text(img, "1 CREDIT", 1, 24, (230, 200, 120, 255), F3)
    save(img, "coindoor-plate")
    save(M.brushed_metal(seed=seed_of("coinmech"), base=(132, 132, 140), direction="v", streak=6, sheen=8), "coinmech")
    img = M.noise_hv((206, 36, 40), 3, seed_of("coinbutton"), S, mottle=3)
    ImageDraw.Draw(img).rectangle([1, 1, 3, 2], fill=(250, 150, 140, 255))
    save(img, "coinbutton")
    save(M.rubber(seed=seed_of("cab-bumper"), base=(30, 28, 34)), "cab-bumper")
    save(M.brushed_metal(seed=seed_of("cab-trim"), base=(120, 122, 132), streak=6, sheen=8), "cab-trim")
    for key, (_, body, _, _) in GAMES.items():
        img = M.painted_metal(seed=seed_of(f"cab-{key}-body"), base=body, grain=2, mottle=3, panel=False, chips=2, under=(60, 46, 34))
        save(img, f"cab-{key}-body")
    save(M.painted_metal(seed=seed_of("cab-themed-body"), base=(16, 14, 22), grain=2, mottle=3, panel=False, chips=2, under=(60, 46, 34)),
         "cab-themed-body")


def cabinet_parts(body, lit=True):
    """Geometry B16 adds to a cabinet (modelled facing north, in gen_3999_arcade.cabinet's frame): the coin door as a
    plate standing off the lower body with two chrome coin entries (each a slot), a red coin button under each and a
    lock; returns (coin door parts, bezel rim parts to turn with the bezel, marquee frame parts, panel bumper parts)."""
    door = [mbox("CoinDoor", (5, 3.5, 2.7), (11, 9.5, 3.0), {"front": "coindoor-plate", "side": body, "top": body, "bottom": body},
                 faces=("north", "east", "west", "up", "down"))]
    door[0]["faces"]["north"]["uv"] = [0, 0, 16, 16]
    for i, x in enumerate((5.6, 8.6)):
        door += [mbox(f"CoinEntry{i}", (x, 6.6, 2.3), (x + 1.8, 9.0, 2.7), "coinmech", faces=("north", "east", "west", "up", "down")),
                 mbox(f"CoinSlot{i}", (x + 0.7, 7.2, 2.25), (x + 1.1, 8.6, 2.3), "black", faces=("north",)),
                 mbox(f"CoinButton{i}", (x + 0.4, 5.6, 2.4), (x + 1.4, 6.3, 2.7), "coinbutton", faces=("north", "east", "west", "up", "down"))]
    door.append(mbox("Lock", (7.7, 8.0, 2.45), (8.3, 8.6, 2.7), "coinmech", faces=("north", "east", "west", "up", "down")))
    rim = [mbox("RimT", (2.5, 21.6, 5.6), (13.5, 22.5, 6.0), "cab-trim", faces=("north", "east", "west", "up", "down")),
           mbox("RimB", (2.5, 15.0, 5.6), (13.5, 16.0, 6.0), "cab-trim", faces=("north", "east", "west", "up", "down")),
           mbox("RimL", (2.5, 16.0, 5.6), (3.6, 21.6, 6.0), "cab-trim", faces=("north", "east")),
           mbox("RimR", (12.4, 16.0, 5.6), (13.5, 21.6, 6.0), "cab-trim", faces=("north", "west"))]
    frame = [mbox("MarqueeTop", (2.4, 27.4, 1.6), (13.6, 27.8, 2.0), "cab-trim", faces=("north", "east", "west", "up", "down")),
             mbox("MarqueeBot", (2.4, 23.2, 1.6), (13.6, 23.6, 2.0), "cab-trim", faces=("north", "east", "west", "up", "down"))]
    bumper = [mbox("Bumper", (1.3, 14.25, 0.2), (14.7, 15.75, 0.5), "cab-bumper", faces=("north", "east", "west", "up", "down")),
              mbox("PanelLip", (1.4, 16.0, 0.5), (14.6, 16.3, 0.9), "cab-bumper", faces=("north", "east", "west", "up", "south"))]
    return door, rim, frame, bumper



# ---------------------------------------------------------------- vending machines

VEND_COLOURS = {"snack": [(255, 74, 0), (240, 196, 30), (209, 59, 247), (100, 232, 247), (255, 42, 90), (90, 200, 90)],
                "drink": [(200, 30, 40), (60, 200, 90), (120, 60, 200), (240, 240, 230), (255, 160, 255)]}


def vending_textures():
    """The inside of a vending machine's window (a dark back wall lit from the top), its wire shelves, and the products'
    packs: one key per colour, a bag or a can with a light label band and a crimp or a rim (B0 painted the rows of
    products flat on the front)."""
    from PIL import ImageDraw
    for kind, body in (("snack", (40, 30, 60)), ("drink", (20, 50, 90))):
        img = M.noise_hv(M.lift(body, -14), 2, seed_of("vendback" + kind), S, mottle=3)
        px = img.load()
        for y in range(S):
            for x in range(S):
                px[x, y] = M.rgba(M.lift(px[x, y], 26 * math.exp(-y / 6.0)), 255)
        save(img, f"vendback-{kind}")
    save(M.brushed_metal(seed=seed_of("vendshelf"), base=(170, 172, 180), streak=6, sheen=8), "vendshelf")
    for kind, cols in VEND_COLOURS.items():
        for i, c in enumerate(cols):
            img = M.noise_hv(c, 2, seed_of(f"vendprod{kind}{i}"), S, mottle=2)
            d = ImageDraw.Draw(img)
            if kind == "snack":
                d.rectangle([0, 0, 31, 3], fill=M.rgba(M.lift(c, -30)))          # the crimped top of a bag
                for x in range(0, 32, 2):
                    d.point([x, 1], fill=M.rgba(M.lift(c, 20)))
                d.rectangle([4, 12, 27, 20], fill=(246, 244, 236, 255))           # the label band
                d.rectangle([7, 14, 24, 18], fill=M.rgba(M.lift(c, -40)))
            else:
                d.rectangle([0, 0, 31, 2], fill=(200, 204, 212, 255))             # a can's rim
                d.rectangle([0, 29, 31, 31], fill=(170, 174, 182, 255))
                d.rectangle([0, 11, 31, 19], fill=(246, 244, 236, 255))
                d.rectangle([3, 13, 28, 17], fill=M.rgba(M.lift(c, -40)))
            for x in range(S):                                                    # a lit edge on the left
                px = img.load()
                for y in range(S):
                    if x < 3:
                        px[x, y] = M.rgba(M.lift(px[x, y], 12 - 4 * x), 255)
            save(img, f"vendprod-{kind}-{i}")


def vending_keypad():
    """The vending machine's keypad as a plate with 3 x 4 keys, and the taped coin slot as a label standing on the front,
    both where B0's picture paints them (its keypad dots at picture x 24-29, y 14-25; the slot at x 23-30, y 28-34)."""
    from gen_3999_kit import picture
    els = [mbox("KeyPlate", (2.35, 19.1, 1.2), (4.75, 24.6, 1.4), "darksteel", faces=("north", "east", "west", "up", "down"))]
    for r in range(4):
        for c in range(3):
            x = 2.6 + c * 0.75
            y = 23.6 - r * 1.3
            els.append(mbox(f"Key{r}{c}", (x, y, 1.0), (x + 0.5, y + 0.8, 1.2), "keybutton", faces=("north", "east", "west", "up", "down")))
    els.append(picture(mbox("Tape", (2.35, 15.1, 1.25), (5.1, 17.9, 1.4), "tape", faces=("north", "east", "west", "up", "down")), "tape"))
    return els


def vending_parts(kind, glow=90):
    """A vending machine facing north whose window is an opening: the front face (B0's picture, its window cut out
    of it) on a frame of four boxes, a lit back wall 2.4 units in, five wire shelves, and on each four packs (bags of
    crisps, or cans and bottles) standing behind the glass. Returns the body and front; the caller adds the glass,
    keypad, tape, flap, top and neon edges as before."""
    body = f"vendingbody-{kind}"
    pic = f"vending-{kind}"
    # A north face shows its texture's left edge at the east (+x) end, so the picture's u runs from x 14.5 down to 1.5:
    # the rows of products (picture x 2..23, y 4..51) are at x 5.2..13.7, under the title
    FX1, FX2, FY1, FY2 = 1.5, 14.5, 1.0, 31.0       # the front picture's extent
    X1, X2, Y1, Y2 = 5.2, 13.7, 7.1, 28.6           # the window

    def uv(x1, y1, x2, y2):
        u = lambda x: round((FX2 - x) / (FX2 - FX1) * 16, 4)
        v = lambda y: round((FY2 - y) / (FY2 - FY1) * 16, 4)
        return [u(x2), v(y2), u(x1), v(y1)]

    def front(name, x1, y1, x2, y2, faces):
        el = mbox(name, (x1, y1, 1.4), (x2, y2, 4.0), {"front": body, "side": "vendshelf", "top": "vendshelf", "bottom": "vendshelf"},
                  faces=("north",) + faces)
        el["faces"]["north"] = {"texture": "#" + pic, "uv": uv(x1, y1, x2, y2), "glow": glow}
        return el

    els = [mbox("Body", (1, 0, 4.0), (15, 31, 15), body),
           mbox("SideW", (1, 0, 2.0), (1.5, 31, 4.0), body, faces=("north", "west", "up", "down")),
           mbox("SideE", (14.5, 0, 2.0), (15, 31, 4.0), body, faces=("north", "east", "up", "down")),
           front("FrontL", FX1, FY1, X1, FY2, ("west", "east", "up", "down")),
           front("FrontR", X2, FY1, FX2, FY2, ("east", "west", "up", "down")),
           front("FrontB", X1, FY1, X2, Y1, ("up",)),
           front("FrontT", X1, Y2, X2, FY2, ("down",))]
    back = mbox("Inside", (X1, Y1, 3.8), (X2, Y2, 4.0), f"vendback-{kind}", faces=("north",))
    back["faces"]["north"]["uv"] = [0, 0, 16, 16]
    back["faces"]["north"]["glow"] = glow
    els.append(back)
    rng = random.Random(seed_of("vendprods" + kind))
    cols = VEND_COLOURS[kind]
    rows = 5
    pitch = (Y2 - Y1) / rows
    for r in range(rows):
        y = Y1 + r * pitch
        els.append(mbox(f"Shelf{r}", (X1, y, 1.6), (X2, y + 0.3, 3.8), "vendshelf", faces=("north", "up")))
        w = (X2 - X1) / 4
        for c in range(4):
            x = X1 + c * w + 0.25
            k = rng.randrange(len(cols))
            if kind == "snack":
                h = rng.uniform(2.6, 3.2)
                els.append(mbox(f"Pack{r}{c}", (x, y + 0.3, 2.2), (x + w - 0.5, y + 0.3 + h, 3.4), f"vendprod-{kind}-{k}",
                                faces=("north", "east", "west", "up")))
            else:
                h = rng.choice((2.4, 3.3))
                cw = 1.3 if h < 3 else 1.1
                for j, dx in enumerate((0.1, w - 0.6 - cw)):
                    els.append(mbox(f"Can{r}{c}{j}", (x + dx, y + 0.3, 2.3), (x + dx + cw, y + 0.3 + h, 3.3), f"vendprod-{kind}-{k}",
                                    faces=("north", "east", "west", "up")))
        for el in els[-8:]:
            if el["name"].startswith(("Pack", "Can")):
                el["faces"]["north"]["glow"] = glow // 2
    return els



def textures():
    marble("marble-white")
    marble("marble-black")
    paint()
    furniture_textures()
    vending_textures()
    print("3999 B16: marble, paint, food court furniture (the cabinets: gen_3999_tex_arcade.generate)")
