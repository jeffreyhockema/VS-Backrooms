"""Level 183, "Clean Sewers" (experimental; tag `183`, id 27, blocks `l183-`): the level's own assets, after
docs/design/experimental-levels/183-plan.md section 3.

    bash tools/locked.sh run python tools/gen_183.py [tex] [blocks] [sounds]   (no argument: all)

Writes only the level's own folders: textures/block/183/, shapes/block/183/, blocktypes/183/ and sounds/ambient/183/
(emptied first, so a renamed code leaves nothing stale behind). Five block codes:

    l183-wall      glazed off-white sewer brick, a pale grey-green course here and there (plain, stained with a few clean
                   mineral streaks, and "tide": the block one up from the walkway, a clean waterline across it)
    l183-floor     pale scored concrete (walkway), the same with a yellow-green edge band (curb), the channels' smooth
                   grey-blue cement bed (bed)
    l183-ceiling   dark grey-green brick (flat over the side tunnels, ringed with a lighter keystone course over the
                   mains, darker headers over the chambers' and halls' domes)
    l183-grate     a black iron floor grate, its bars see-through to the water under it (the bridges, the decks, the drains)
    l183-lamp      a caged white tube on a wall bracket (on, bright, flicker, off; by the side it faces)

Everything else is reused (Level 2's pipes, Level 1's pillar, vanilla still water). The one new sound is the running
water in brick; the drips, laps and the channels' wash are the Poolrooms'.
"""
import json
import os
import shutil
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import matlib as M  # noqa: E402
import texlib  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
TEX = os.path.join(ASSETS, "textures", "block", "183")
SHAPES = os.path.join(ASSETS, "shapes", "block", "183")
BLOCKS = os.path.join(ASSETS, "blocktypes", "183")
SOUNDS = os.path.join(ASSETS, "sounds", "ambient", "183")

# The palette: clean, cool, pale (the fog is #c9d6d6)
GLAZE = (214, 218, 210)
GLAZE_GREEN = (184, 200, 188)
GROUT = (158, 162, 154)
WALK = (176, 178, 170)
BAND = (170, 178, 92)
BED = (120, 134, 142)
VAULT = (82, 96, 88)
VAULT_MORTAR = (64, 72, 68)
KEY = (128, 140, 128)
IRON = (34, 36, 38)


def fresh(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path)


def save(img, name):
    assert img.size[0] % 8 == 0 and img.size[1] % 8 == 0, name
    img.save(os.path.join(TEX, name + ".png"))


# ======================================================================== Textures

def wall(seed, tones, stained=False, tide=False):
    """Glazed brick: oblong tiles 16 by 8 in a running bond, one course in four the pale green (a band round the tunnels)."""
    img = M.tile(seed=1830, base=GLAZE, grout=GROUT, pitch=(16, 8), offset=0.5, jitter=5, uneven=3, crazing=0.15)
    # The green course (rows 16-23 of the texture), each tile lifted to the green glaze
    px = img.load()
    for y in range(16, 23):
        for x in range(32):
            if (x + (8 if (y // 8) % 2 else 0)) % 16 == 15:
                continue
            r, g, b, a = px[x, y]
            px[x, y] = (M.clamp(r - 30), M.clamp(g - 18), M.clamp(b - 24), a)
    M.hue_jitter(img, 3, seed=tones, cell=8)
    if stained:
        # Clean as it is, a few pale mineral streaks where water has run down the joints
        M.drips(img, n=3, seed=seed + 1, color=(190, 196, 176), length=(8, 20), strength=0.35)
        M.grime(img, 0.08, seed=seed + 2, color=(150, 160, 150), cells=(8, 4), cover=0.4)
    if tide:
        # The waterline: a crisp, clean line low on the block, the glaze a touch darker and greener under it
        M.tideline(img, 22, seed=seed + 3, color=(108, 138, 132), amount=0.6, wave=0.6, below=0.5)
    return img


def walkway(seed, cracks=0):
    img = M.concrete(seed=seed, base=WALK, grain=3, mottle=6, aggregate=0.05, pores=0.01, cracks=cracks, patches=3, patch_hue=2)
    # Scored into slabs: a groove every 16 px each way
    M.emboss_lines(img, xs=(0, 16), ys=(0, 16), raised=False, strength=0.16)
    M.grime(img, 0.05, seed=seed + 1, color=(140, 146, 140), cells=(8, 4), cover=0.4)
    return img


def curb(seed):
    img = walkway(seed)
    # The yellow-green safety band round its edge (it shows along the channel whichever way the curb runs)
    px = img.load()
    for y in range(32):
        for x in range(32):
            d = min(x, y, 31 - x, 31 - y)
            if d < 4:
                r, g, b, a = px[x, y]
                t = 0.75 if d < 3 else 0.35
                px[x, y] = (M.clamp(r + (BAND[0] - r) * t), M.clamp(g + (BAND[1] - g) * t), M.clamp(b + (BAND[2] - b) * t), a)
    M.scratches(img, n=4, seed=seed + 2, length=(2, 5), light=0.12)
    return img


def bed(seed):
    img = M.concrete(seed=seed, base=BED, grain=3, mottle=5, aggregate=0.03, pores=0.006, swirl=0.4, patches=3, patch_hue=3)
    M.grime(img, 0.08, seed=seed + 1, color=(104, 118, 120), cells=(8, 4), cover=0.5)
    return img


def vault(seed, tones, keystone=False, dark=False):
    base = (VAULT[0] - 10, VAULT[1] - 10, VAULT[2] - 10) if dark else VAULT
    img = M.brick(seed=1840, base=base, mortar=VAULT_MORTAR, course=8, length=16, offset=0.5, jitter=8, hue=3, pits=0.03,
                  grain=4, mottle=6, tones=tones)
    if keystone:
        # The rings' lighter keystone course down the middle of the vault
        px = img.load()
        for y in range(12, 19):
            for x in range(32):
                r, g, b, a = px[x, y]
                px[x, y] = (M.clamp(r + (KEY[0] - r) * 0.45), M.clamp(g + (KEY[1] - g) * 0.45), M.clamp(b + (KEY[2] - b) * 0.45), a)
    M.grime(img, 0.06, seed=seed, color=(60, 70, 66), cells=(8, 4), cover=0.4)
    return img


def textures():
    fresh(TEX)
    save(wall(11, 1), "wall-plain")
    save(wall(12, 2), "wall-plain-2")
    save(wall(13, 3), "wall-plain-3")
    save(wall(21, 4, stained=True), "wall-stained")
    save(wall(22, 5, stained=True), "wall-stained-2")
    save(wall(31, 6, tide=True), "wall-tide")
    save(wall(32, 7, tide=True), "wall-tide-2")
    save(walkway(41), "floor-walkway")
    save(walkway(42), "floor-walkway-2")
    save(walkway(43, cracks=1), "floor-walkway-3")
    save(curb(51), "floor-curb")
    save(curb(52), "floor-curb-2")
    save(bed(61), "floor-bed")
    save(bed(62), "floor-bed-2")
    save(vault(71, 1), "ceiling-flat")
    save(vault(72, 2), "ceiling-flat-2")
    save(vault(73, 3, keystone=True), "ceiling-arch")
    save(vault(74, 4, keystone=True), "ceiling-arch-2")
    save(vault(75, 5, dark=True), "ceiling-dome")
    save(vault(76, 6, dark=True), "ceiling-dome-2")
    iron = M.painted_metal(seed=81, base=IRON, panel=False, chips=1, under=(70, 66, 60))
    M.rust(iron, 0.08, seed=82, cells=(4, 2))
    save(iron, "grate")
    metal = M.painted_metal(seed=91, base=(196, 200, 198), panel=False, chips=1, under=(120, 120, 116))
    save(metal, "lamp-metal")
    save(texlib.vertical_gradient((250, 254, 255), (214, 232, 240)), "lamp-lit")
    dead = M.noise_hv((150, 156, 158), 3, seed=93, mottle=3)
    save(dead, "lamp-off")
    print("textures:", len(os.listdir(TEX)))


# ======================================================================== Shapes and blocks

def face(tex, uv, glow=0):
    f = {"texture": "#" + tex, "uv": uv}
    if glow:
        f["glow"] = glow
    return f


def box(name, frm, to, tex, glow=0, faces=None):
    dx, dy, dz = to[0] - frm[0], to[1] - frm[1], to[2] - frm[2]
    uv = {"north": [frm[0], 16 - to[1], frm[0] + dx, 16 - frm[1]], "south": [frm[0], 16 - to[1], frm[0] + dx, 16 - frm[1]],
          "east": [frm[2], 16 - to[1], frm[2] + dz, 16 - frm[1]], "west": [frm[2], 16 - to[1], frm[2] + dz, 16 - frm[1]],
          "up": [frm[0], frm[2], frm[0] + dx, frm[2] + dz], "down": [frm[0], frm[2], frm[0] + dx, frm[2] + dz]}
    return {"name": name, "from": frm, "to": to, "faces": {k: face(tex, v, glow) for k, v in uv.items() if faces is None or k in faces}}


def grate_shape():
    """A floor grate across the top of the block: a frame and bars two px deep, open between them (the water shows)."""
    els = [
        box("FrameN", [0, 14, 0], [16, 16, 1.5], "iron"),
        box("FrameS", [0, 14, 14.5], [16, 16, 16], "iron"),
        box("FrameW", [0, 14, 1.5], [1.5, 16, 14.5], "iron"),
        box("FrameE", [14.5, 14, 1.5], [16, 16, 14.5], "iron"),
        box("Cross", [1.5, 14, 7.25], [14.5, 15, 8.75], "iron"),
    ]
    for k, x in enumerate((3.5, 6.25, 9, 11.75)):
        els.append(box(f"Bar{k}", [x, 14.25, 1.5], [x + 1.25, 16, 14.5], "iron"))
    return {"textureWidth": 16, "textureHeight": 16, "textures": {"iron": "backrooms:block/183/grate"}, "elements": els}


def lamp_shape(lit):
    """A caged tube on a wall bracket, its back to the south side of the block (the "north" variant faces north)."""
    tube = "tube"
    els = [
        box("Plate", [3, 9, 15], [13, 13, 16], "metal"),
        box("ArmW", [4, 10.5, 12.5], [5, 11.5, 15], "metal"),
        box("ArmE", [11, 10.5, 12.5], [12, 11.5, 15], "metal"),
        box("CapW", [2.5, 9.5, 11], [3.5, 12.5, 14], "metal"),
        box("CapE", [12.5, 9.5, 11], [13.5, 12.5, 14], "metal"),
        box("Tube", [3.5, 10, 11.5], [12.5, 12, 13.5], tube, 200 if lit else 0),
        box("CageTop", [3.5, 12.25, 11], [12.5, 12.75, 14], "metal", faces=("up", "down", "north", "south")),
        box("CageFront", [3.5, 10.75, 10.75], [12.5, 11.25, 11.25], "metal"),
        box("CageLow", [3.5, 9.25, 11.5], [12.5, 9.75, 13.5], "metal"),
    ]
    for k, x in enumerate((5.75, 8, 10.25)):
        els.append(box(f"Rib{k}", [x, 9.25, 10.75], [x + 0.5, 12.75, 11.25], "metal"))
    return {"textureWidth": 16, "textureHeight": 16,
            "textures": {"metal": "backrooms:block/183/lamp-metal", "tube": "backrooms:block/183/lamp-" + ("lit" if lit else "off")},
            "elements": els}


def write_json(path, data, comment=None):
    text = json.dumps(data, indent="\t", ensure_ascii=False)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        if comment:
            f.write("// " + comment + "\n")
        f.write(text + "\n")


STONE_SOUNDS = {"walk": "game:walk/stone", "place": "game:block/loosestone", "break": "game:block/rock-break-pickaxe", "hit": "game:block/rock-hit-pickaxe"}
METAL_SOUNDS = {"walk": "game:walk/stone", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"}


def alts(base, extra, rotate=False):
    """A texture with its alternates: the extra versions (and, for floors, every one turned)."""
    out = []
    for n in [base] + extra:
        for r in ((0, 90, 180, 270) if rotate else (0,)):
            if n == base and r == 0:
                continue
            a = {"base": "block/183/" + n}
            if r:
                a["rotation"] = r
            out.append(a)
    return {"base": "block/183/" + base, "alternates": out} if out else {"base": "block/183/" + base}


def cube_block(code, states, textures, comment, extra=None):
    data = {"code": code, "variantgroups": [{"code": "type", "states": states}],
            "creativeinventory": {"general": ["*"], "construction": ["*"]}, "blockmaterial": "Stone", "drawtype": "cube",
            "texturesByType": {f"*-{s}": {"all": t} for s, t in textures.items()},
            "resistance": 8, "requiredMiningTier": 3, "lightAbsorption": 99, "sounds": STONE_SOUNDS}
    if extra:
        data.update(extra)
    write_json(os.path.join(BLOCKS, code + ".json"), data, comment)


SIDES = ("north", "east", "south", "west")
ROT = {"north": 0, "east": 270, "south": 180, "west": 90}


def lamp_box(side):
    """The lamp's box, against the wall behind it (south of a north-facing lamp)."""
    x1, x2, y1, y2, d = 2.5 / 16, 13.5 / 16, 9 / 16, 13 / 16, 5.25 / 16
    return {
        "north": {"x1": x1, "y1": y1, "z1": 1 - d, "x2": x2, "y2": y2, "z2": 1},
        "south": {"x1": x1, "y1": y1, "z1": 0, "x2": x2, "y2": y2, "z2": d},
        "east": {"x1": 0, "y1": y1, "z1": x1, "x2": d, "y2": y2, "z2": x2},
        "west": {"x1": 1 - d, "y1": y1, "z1": x1, "x2": 1, "y2": y2, "z2": x2},
    }[side]


def blocks():
    fresh(BLOCKS)
    fresh(SHAPES)
    cube_block("l183-wall", ["plain", "stained", "tide"], {
        "plain": alts("wall-plain", ["wall-plain-2", "wall-plain-3"]),
        "stained": alts("wall-stained", ["wall-stained-2"]),
        "tide": alts("wall-tide", ["wall-tide-2"]),
    }, "Level 183: glazed sewer brick (plain, stained; tide: the clean waterline one block up from the walkway)")
    cube_block("l183-floor", ["walkway", "curb", "bed"], {
        "walkway": alts("floor-walkway", ["floor-walkway-2", "floor-walkway-3"], rotate=True),
        "curb": alts("floor-curb", ["floor-curb-2"]),
        "bed": alts("floor-bed", ["floor-bed-2"], rotate=True),
    }, "Level 183: pale scored concrete walkways, the curbs' yellow-green band, the channels' grey-blue cement bed")
    cube_block("l183-ceiling", ["flat", "arch", "dome"], {
        "flat": alts("ceiling-flat", ["ceiling-flat-2"]),
        "arch": alts("ceiling-arch", ["ceiling-arch-2"]),
        "dome": alts("ceiling-dome", ["ceiling-dome-2"]),
    }, "Level 183: the sewers' grey-green brick vault (flat; arch: the mains' rings with a keystone course; dome)")

    write_json(os.path.join(SHAPES, "grate.json"), grate_shape())
    write_json(os.path.join(BLOCKS, "l183-grate.json"), {
        "code": "l183-grate",
        "creativeinventory": {"general": ["*"], "construction": ["*"]},
        "blockmaterial": "Metal", "drawtype": "json",
        "shape": {"base": "block/183/grate"},
        "textures": {"iron": {"base": "block/183/grate"}},
        "sidesolid": {"all": False, "up": True}, "sideopaque": {"all": False},
        "collisionbox": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 1, "z2": 1},
        "selectionbox": {"x1": 0, "y1": 0.875, "z1": 0, "x2": 1, "y2": 1, "z2": 1},
        "lightAbsorption": 0, "resistance": 8, "requiredMiningTier": 3, "sounds": METAL_SOUNDS,
    }, "Level 183: a black iron floor grate over the water (the bridges, the crossings' decks, the drains); walked on as a full block")

    write_json(os.path.join(SHAPES, "lamp-lit.json"), lamp_shape(True))
    write_json(os.path.join(SHAPES, "lamp-off.json"), lamp_shape(False))
    states = ("on", "bright", "flicker", "off")
    shapes, boxes, attrs = {}, {}, {}
    for st in states:
        for s in SIDES:
            shapes[f"*-{st}-{s}"] = {"base": "block/183/lamp-" + ("off" if st == "off" else "lit"), "rotateY": ROT[s]}
            boxes[f"*-{st}-{s}"] = lamp_box(s)
    for s in SIDES:
        attrs[f"*-flicker-{s}"] = {"offBlock": f"backrooms:l183-lamp-off-{s}"}
    # Light: clean, cool white; a flickering tube keeps its light (the block entity only swaps its look)
    write_json(os.path.join(BLOCKS, "l183-lamp.json"), {
        "code": "l183-lamp",
        "variantgroups": [{"code": "state", "states": list(states)}, {"code": "side", "states": list(SIDES)}],
        "creativeinventory": {"general": ["*-on-north"], "decorative": ["*-on-north"]},
        "blockmaterial": "Glass", "drawtype": "json",
        "shapeByType": shapes,
        "lightHsvByType": {"*-on-*": [34, 1, 12], "*-bright-*": [34, 1, 14], "*-flicker-*": [34, 1, 11]},
        "entityClassByType": {"*-flicker-*": "BackroomsFlicker"},
        "attributesByType": attrs,
        "dropsByType": {"*": [{"type": "item", "code": "glassshard", "quantity": {"avg": 0.5, "var": 0}},
                              {"type": "item", "code": "scrapwire", "quantity": {"avg": 0.5, "var": 0}}]},
        "sidesolid": {"all": False}, "sideopaque": {"all": False},
        "collisionboxByType": boxes, "selectionboxByType": boxes,
        "lightAbsorption": 0, "resistance": 0.5,
        "sounds": {"place": "game:block/glass", "break": "game:block/glass", "hit": "game:block/glass"},
    }, "Level 183: a caged white tube on a wall bracket (on, bright, flicker, off; the side it faces, its wall behind it)")
    print("blocktypes:", sorted(os.listdir(BLOCKS)))


# ======================================================================== Sound

def sounds():
    """Running water in brick, a seamless 16 s loop: a steady wash of water along a channel (filtered noise that swells
    slowly in whole cycles), small gurgles where it runs over a lip, a low tone of the tunnel itself, and the hard, short
    reflections of glazed brick."""
    from gen_entity_sounds import RATE, band
    from gen_level_sounds import tile_room
    from oggutil import write_ogg
    fresh(SOUNDS)
    rng = np.random.default_rng(18301)
    n = int(16.0 * RATE)
    t = np.arange(n) / RATE
    f = np.fft.rfftfreq(n, 1 / RATE)

    def bed_noise(shape):
        spec = (rng.normal(size=len(f)) + 1j * rng.normal(size=len(f))) * shape
        out = np.fft.irfft(spec, n=n)
        return out / max(1e-9, np.max(np.abs(out)))
    wash = bed_noise(np.exp(-((f - 600) / 450) ** 2) + 0.45 * np.exp(-((f - 1800) / 900) ** 2) + 0.15 * np.exp(-((f - 4200) / 1500) ** 2))
    rumble = bed_noise(np.exp(-((f - 70) / 45) ** 2))
    # Swells in whole cycles over the loop, two rates so it never quite repeats inside it
    wash *= 0.7 + 0.18 * np.sin(2 * np.pi * t * 3 / 16.0) + 0.12 * np.sin(2 * np.pi * t * 7 / 16.0 + 1.0)
    tone = 0.18 * np.sin(2 * np.pi * 55 * t) + 0.08 * np.sin(2 * np.pi * 110 * t)
    out = 0.8 * wash + 0.35 * rumble + tone * (0.8 + 0.2 * np.sin(2 * np.pi * t * 2 / 16.0))
    # Gurgles: short bubbling bursts, wrapped round the loop's end
    for k in range(26):
        d = int(rng.uniform(0.05, 0.16) * RATE)
        s = np.arange(d) / RATE
        f0 = rng.uniform(250, 700)
        burst = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.6 * np.sin(2 * np.pi * s * rng.uniform(25, 45)))) / RATE)
        burst *= np.sin(np.pi * s / s[-1]) ** 2
        at = int(rng.uniform(0, 16.0) * RATE)
        idx = (np.arange(d) + at) % n
        out[idx] += rng.uniform(0.04, 0.12) * burst
    out = tile_room(band(out, 30, 9000), 0.22)
    out = 0.5 * out / max(1e-9, np.max(np.abs(out)))
    path = os.path.join(SOUNDS, "sewer.ogg")
    if write_ogg(path, out, RATE):
        print("wrote", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    what = set(sys.argv[1:]) or {"tex", "blocks", "sounds"}
    if "tex" in what:
        textures()
    if "blocks" in what:
        blocks()
    if "sounds" in what:
        sounds()
