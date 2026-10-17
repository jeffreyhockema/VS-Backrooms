"""The Basement (experimental, unnumbered; tag `basement`, id 22, blocks `basement-`): the level's own assets, after
docs/design/experimental-levels/basement-plan.md section 3.

    bash tools/locked.sh run python tools/gen_basement.py [tex] [blocks] [sounds]   (no argument: all)

Writes only the level's own folders: textures/block/basement/, shapes/block/basement/, blocktypes/basement/ and
sounds/ambient/basement/ (emptied first, so a renamed code leaves nothing stale behind). Six block codes:

    basement-wall     damp painted cinder block, dark green-grey, rust runs from its ties (plain, stained, and "tide"
                      with a tide line low on it: the Flood's wall just over the water)
    basement-floor    bare cracked concrete (dry, damp), the Dry Patch's swept floor (patch)
    basement-ceiling  low concrete with the shadows of its form boards (plain, drip-stained)
    basement-steps    wet concrete steps with a rust line along their nosing (the concrete stairs' shape)
    basement-slime    green-brown slime over concrete: the Flood's walls under the water (wall) and its bed (bed)
    basement-lamp     a bare bulb in a wire cage on its cable (on, dim, bright, flicker, off)

Everything else is reused (Level 1's crates and pillar, Level 2's pipes, drums and cabinets, Level 5's boiler, the
detail kit's hand pump, vanilla still water). The one new sound is the Cellar's room tone; the Flood uses the Poolrooms'
wash and its drips and laps.
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
TEX = os.path.join(ASSETS, "textures", "block", "basement")
SHAPES = os.path.join(ASSETS, "shapes", "block", "basement")
BLOCKS = os.path.join(ASSETS, "blocktypes", "basement")
SOUNDS = os.path.join(ASSETS, "sounds", "ambient", "basement")

# The palette: the fog is #0d1614, so everything sits in cold green-greys
CINDER = (92, 102, 95)
MORTAR = (74, 80, 76)
CONCRETE = (98, 100, 95)
CEILING = (104, 106, 101)
RUST = (122, 72, 40)
RUSTDARK = (78, 48, 30)
DAMP = (52, 58, 54)
SLIME = (58, 72, 44)
SLIMEDARK = (38, 46, 30)
SILT = (66, 62, 48)


def fresh(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path)


def save(img, name):
    assert img.size[0] % 8 == 0 and img.size[1] % 8 == 0, name
    img.save(os.path.join(TEX, name + ".png"))


# ======================================================================== Textures

def wall(seed, stained=0.0, tide=False):
    img = M.brick(seed=1100, base=CINDER, mortar=MORTAR, course=8, length=16, chamfer=True, jitter=7, hue=3, pits=0.04,
                  grain=4, mottle=6, tones=seed)
    # Old paint gone chalky in patches, damp creeping up from below
    M.grime(img, 0.18, seed=seed + 1, color=(118, 124, 116), cells=(8, 4), cover=0.35)
    M.grime(img, 0.12 + 0.2 * stained, seed=seed + 2, color=DAMP, cells=(8, 4, 2), cover=0.45 + 0.3 * stained)
    # Rust runs from the ties, down the face
    M.drips(img, n=1 + int(3 * stained), seed=seed + 3, color=RUST, length=(8, 22), strength=0.35 + 0.2 * stained)
    if stained:
        M.drips(img, n=3, seed=seed + 4, color=DAMP, length=(10, 30), strength=0.4, width=2)
    if tide:
        # The Flood's wall just over the water: a dark wet band along the bottom under a ragged tide line
        M.tideline(img, 23, seed=seed + 5, color=SLIMEDARK, amount=0.55, wave=1.2, below=0.9)
        M.grime(img, 0.25, seed=seed + 6, color=SLIME, cells=(4, 2), bias="bottom", cover=0.7)
    return img


def floor(seed, damp=False, cracks=0):
    img = M.concrete(seed=seed, base=CONCRETE, grain=4, mottle=8, aggregate=0.08, pores=0.015, cracks=cracks, patches=5, patch_hue=2)
    M.grime(img, 0.12, seed=seed + 1, color=(70, 72, 66), cells=(8, 4), cover=0.5)
    if damp:
        for k, at in enumerate(M.spread(seed + 2, 2)):
            M.stain(img, seed=seed + 3 + k, radius=10, color=DAMP, strength=0.45, at=at, ring=0.4)
    return img


def patch_floor(seed):
    # Swept, a little lighter and warmer: the one place anyone has looked after
    img = M.concrete(seed=seed, base=(112, 110, 102), grain=3, mottle=6, aggregate=0.06, pores=0.01, swirl=0.6, patches=3)
    M.grime(img, 0.1, seed=seed + 1, color=(92, 86, 70), cells=(8, 4), cover=0.4)
    return img


def ceiling(seed, stained=False):
    img = M.concrete(seed=seed, base=CEILING, grain=3, mottle=7, aggregate=0.05, pores=0.02, joints=(15, 31), patches=4)
    M.ao_border(img, 2, 0.12, sides="tb")
    if stained:
        at = M.spread(seed + 1, 1)[0]
        M.stain(img, seed=seed + 2, radius=11, color=(96, 84, 58), strength=0.5, at=at, ring=0.7)
        M.drips(img, n=2, seed=seed + 3, color=RUSTDARK, length=(4, 9), strength=0.3)
    return img


def steps(seed):
    img = M.concrete(seed=seed, base=(84, 88, 84), grain=4, mottle=6, aggregate=0.08, pores=0.01, patches=3)
    M.grime(img, 0.25, seed=seed + 1, color=SLIMEDARK, cells=(8, 4), cover=0.55)
    # The wet shine along the edge of a tread, and a rust line where an old nosing strip was
    for x in range(32):
        M.touch(img, x, 1, 0.12)
        M.touch(img, x, 2, 0.06)
        M.touch(img, x, 17, 0.1)
    M.rust(img, 0.12, seed=seed + 2, color=RUST, dark=RUSTDARK, pits=False, cells=(8, 4))
    return img


def slime(seed, bed=False):
    base = SILT if bed else (70, 78, 66)
    img = M.concrete(seed=seed, base=base, grain=5, mottle=9, aggregate=0.06, pores=0.02, patches=6)
    # An algae film: patchy green over the concrete, a darker crust, a few pale specks of sediment
    M.grime(img, 0.45, seed=seed + 1, color=SLIME, cells=(8, 4, 2), cover=0.75)
    M.grime(img, 0.3, seed=seed + 2, color=SLIMEDARK, cells=(4, 2), cover=0.45)
    if bed:
        for k, at in enumerate(M.spread(seed + 3, 2)):
            M.stain(img, seed=seed + 4 + k, radius=8, color=(40, 36, 26), strength=0.35, at=at, ring=0.2)
    else:
        M.drips(img, n=4, seed=seed + 5, color=SLIMEDARK, length=(12, 30), strength=0.35, width=2)
    return img


def textures():
    fresh(TEX)
    save(wall(11), "wall-plain")
    save(wall(12), "wall-plain-2")
    save(wall(13, stained=0.6), "wall-plain-3")
    save(wall(21, stained=1.0), "wall-stained")
    save(wall(22, stained=1.0), "wall-stained-2")
    save(wall(31, stained=0.8, tide=True), "wall-tide")
    save(wall(32, stained=0.8, tide=True), "wall-tide-2")
    save(floor(41), "floor-dry")
    save(floor(42), "floor-dry-2")
    save(floor(43, cracks=2), "floor-dry-3")
    save(floor(51, damp=True), "floor-damp")
    save(floor(52, damp=True, cracks=1), "floor-damp-2")
    save(patch_floor(61), "floor-patch")
    save(ceiling(71), "ceiling-plain")
    save(ceiling(72), "ceiling-plain-2")
    save(ceiling(73, stained=True), "ceiling-stained")
    save(steps(81), "steps")
    save(slime(91), "slime-wall")
    save(slime(92), "slime-wall-2")
    save(slime(93, bed=True), "slime-bed")
    save(slime(94, bed=True), "slime-bed-2")
    # The lamp's cage and its bulb (lit warm, the dead one grey)
    cage = M.painted_metal(seed=101, base=(58, 56, 52), panel=False, chips=2, under=(96, 70, 48))
    M.rust(cage, 0.3, seed=102, color=RUST, dark=RUSTDARK, cells=(4, 2))
    save(cage, "cage")
    lit = texlib.vertical_gradient((255, 236, 170), (232, 196, 120))
    save(lit, "bulb-lit")
    dead = M.noise_hv((92, 90, 84), 3, seed=103, mottle=4)
    M.grime(dead, 0.3, seed=104, color=(60, 56, 48), cells=(4, 2), cover=0.6)
    save(dead, "bulb-off")
    print("textures:", len(os.listdir(TEX)))


# ======================================================================== Shapes and blocks

def face(tex, uv, glow=0):
    f = {"texture": "#" + tex, "uv": uv}
    if glow:
        f["glow"] = glow
    return f


def box(name, frm, to, tex, glow=0):
    dx, dy, dz = to[0] - frm[0], to[1] - frm[1], to[2] - frm[2]
    uv = {"north": [0, 0, dx, dy], "south": [0, 0, dx, dy], "east": [0, 0, dz, dy], "west": [0, 0, dz, dy],
          "up": [0, 0, dx, dz], "down": [0, 0, dx, dz]}
    return {"name": name, "from": frm, "to": to, "faces": {k: face(tex, v, glow) for k, v in uv.items()}}


def lamp_shape(lit):
    """A bare bulb on its cable, in a wire cage of four bars and two rings, hanging from the ceiling block above."""
    bulb = "bulb"
    els = [
        box("Cable", [7.75, 9, 7.75], [8.25, 16, 8.25], "cage"),
        box("Socket", [7, 7.5, 7], [9, 9, 9], "cage"),
        box("Bulb", [6.5, 4, 6.5], [9.5, 7.5, 9.5], bulb, 160 if lit else 0),
        box("RingTop", [5.5, 7.5, 5.5], [10.5, 8, 10.5], "cage"),
        box("RingBottom", [5.5, 3, 5.5], [10.5, 3.5, 10.5], "cage"),
    ]
    for k, (x, z) in enumerate(((5.5, 5.5), (10, 5.5), (5.5, 10), (10, 10))):
        els.append(box(f"Bar{k}", [x, 3.5, z], [x + 0.5, 7.5, z + 0.5], "cage"))
    return {"textureWidth": 16, "textureHeight": 16,
            "textures": {"cage": "backrooms:block/basement/cage", "bulb": "backrooms:block/basement/bulb-" + ("lit" if lit else "off")},
            "elements": els}


def write_json(path, data, comment=None):
    text = json.dumps(data, indent="\t", ensure_ascii=False)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        if comment:
            f.write("// " + comment + "\n")
        f.write(text + "\n")


STONE_SOUNDS = {"walk": "game:walk/stone", "place": "game:block/loosestone", "break": "game:block/rock-break-pickaxe", "hit": "game:block/rock-hit-pickaxe"}


def alts(base, extra, rotate=False):
    """A texture with its alternates: the extra versions (and, for floors, every one turned)."""
    names = [base] + extra
    out = []
    for n in names:
        for r in ((0, 90, 180, 270) if rotate else (0,)):
            if n == base and r == 0:
                continue
            a = {"base": "block/basement/" + n}
            if r:
                a["rotation"] = r
            out.append(a)
    return {"base": "block/basement/" + base, "alternates": out} if out else {"base": "block/basement/" + base}


def cube_block(code, states, textures, comment, extra=None):
    data = {"code": code, "variantgroups": [{"code": "type", "states": states}],
            "creativeinventory": {"general": ["*"], "construction": ["*"]}, "blockmaterial": "Stone", "drawtype": "cube",
            "texturesByType": {f"*-{s}": {"all": t} for s, t in textures.items()},
            "resistance": 8, "requiredMiningTier": 3, "lightAbsorption": 99, "sounds": STONE_SOUNDS}
    if extra:
        data.update(extra)
    write_json(os.path.join(BLOCKS, code + ".json"), data, comment)


def blocks():
    fresh(BLOCKS)
    fresh(SHAPES)
    cube_block("basement-wall", ["plain", "stained", "tide"], {
        "plain": alts("wall-plain", ["wall-plain-2", "wall-plain", "wall-plain-2", "wall-plain-3"]),
        "stained": alts("wall-stained", ["wall-stained-2"]),
        "tide": alts("wall-tide", ["wall-tide-2"]),
    }, "The Basement: damp painted cinder block (plain, stained; tide: the Flood's wall just over the water)")
    cube_block("basement-floor", ["dry", "damp", "patch"], {
        "dry": alts("floor-dry", ["floor-dry-2", "floor-dry-3"], rotate=True),
        "damp": alts("floor-damp", ["floor-damp-2", "floor-dry"], rotate=True),
        "patch": alts("floor-patch", [], rotate=True),
    }, "The Basement: the Cellar's bare concrete floor (dry, damp) and the Dry Patch's")
    cube_block("basement-ceiling", ["plain", "stained"], {
        "plain": alts("ceiling-plain", ["ceiling-plain-2"]),
        "stained": alts("ceiling-stained", ["ceiling-plain"]),
    }, "The Basement: the low concrete ceiling (plain, drip-stained)")
    cube_block("basement-slime", ["wall", "bed"], {
        "wall": alts("slime-wall", ["slime-wall-2"]),
        "bed": alts("slime-bed", ["slime-bed-2"], rotate=True),
    }, "The Basement: slime over concrete, the Flood's walls under the water and its bed",
        {"sounds": {"walk": "game:walk/sludge*", "place": "game:block/loosestone", "break": "game:block/rock-break-pickaxe", "hit": "game:block/rock-hit-pickaxe"}})

    rot = {"north": 0, "east": 270, "south": 180, "west": 90}
    boxes = {
        "north": [{"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.5, "z2": 1}, {"x1": 0, "y1": 0.5, "z1": 0, "x2": 1, "y2": 1, "z2": 0.5}],
        "east": [{"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.5, "z2": 1}, {"x1": 0.5, "y1": 0.5, "z1": 0, "x2": 1, "y2": 1, "z2": 1}],
        "south": [{"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.5, "z2": 1}, {"x1": 0, "y1": 0.5, "z1": 0.5, "x2": 1, "y2": 1, "z2": 1}],
        "west": [{"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.5, "z2": 1}, {"x1": 0, "y1": 0.5, "z1": 0, "x2": 0.5, "y2": 1, "z2": 1}],
    }
    write_json(os.path.join(BLOCKS, "basement-steps.json"), {
        "code": "basement-steps",
        "variantgroups": [{"code": "side", "states": ["north", "east", "south", "west"]}],
        "creativeinventory": {"general": ["*-north"], "construction": ["*-north"]},
        "blockmaterial": "Stone", "drawtype": "json",
        "shapeByType": {f"*-{s}": {"base": "block/concretestairs", "rotateY": r} for s, r in rot.items()},
        "textures": {"concrete": {"base": "block/basement/steps"}},
        "collisionSelectionBoxesByType": {f"*-{s}": b for s, b in boxes.items()},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0,
        "resistance": 8, "requiredMiningTier": 3, "sounds": STONE_SOUNDS,
    }, "The Basement: wet concrete steps down into the Flood; the variant is the way they climb (the concrete stairs' shape)")

    write_json(os.path.join(SHAPES, "lamp-lit.json"), lamp_shape(True))
    write_json(os.path.join(SHAPES, "lamp-off.json"), lamp_shape(False))
    # Light: the Cellar's bulbs, the Flood's dim ones far apart, the Dry Patch's one bright bulb; a flickering bulb keeps
    # its light (the block entity only swaps its look)
    write_json(os.path.join(BLOCKS, "basement-lamp.json"), {
        "code": "basement-lamp",
        "variantgroups": [{"code": "state", "states": ["on", "dim", "bright", "flicker", "off"]}],
        "creativeinventory": {"general": ["*-on"], "decorative": ["*-on"]},
        "blockmaterial": "Glass", "drawtype": "json",
        "shapeByType": {"*-off": {"base": "block/basement/lamp-off"}, "*": {"base": "block/basement/lamp-lit"}},
        "lightHsvByType": {"*-on": [7, 4, 11], "*-dim": [7, 4, 7], "*-bright": [7, 3, 14], "*-flicker": [7, 4, 10]},
        "entityClassByType": {"*-flicker": "BackroomsFlicker"},
        "attributesByType": {"*-flicker": {"offBlock": "backrooms:basement-lamp-off"}},
        "dropsByType": {"*": [{"type": "item", "code": "glassshard", "quantity": {"avg": 0.5, "var": 0}},
                              {"type": "item", "code": "scrapwire", "quantity": {"avg": 0.5, "var": 0}}]},
        "sidesolid": {"all": False}, "sideopaque": {"all": False},
        "collisionbox": {"x1": 0.34, "y1": 0.18, "z1": 0.34, "x2": 0.66, "y2": 1, "z2": 0.66},
        "selectionbox": {"x1": 0.34, "y1": 0.18, "z1": 0.34, "x2": 0.66, "y2": 1, "z2": 0.66},
        "lightAbsorption": 0, "resistance": 0.5,
        "sounds": {"place": "game:block/glass", "break": "game:block/glass", "hit": "game:block/glass"},
    }, "The Basement: a bare bulb in a wire cage on its cable (on, dim, bright, flicker, off)")
    print("blocktypes:", sorted(os.listdir(BLOCKS)))


# ======================================================================== Sound

def sounds():
    """The Cellar's room tone, a seamless 16 s loop: a low, close rumble (a boiler somewhere through the walls, its slow
    throb), the hiss of a damp space, and a few drips falling far off in it."""
    from gen_entity_sounds import RATE, band, seconds
    from oggutil import write_ogg
    fresh(SOUNDS)
    rng = np.random.default_rng(2201)
    n = int(16.0 * RATE)
    t = np.arange(n) / RATE
    # Seamless noise beds: shaped in the frequency domain over the whole loop
    f = np.fft.rfftfreq(n, 1 / RATE)

    def bed(shape):
        spec = (rng.normal(size=len(f)) + 1j * rng.normal(size=len(f))) * shape
        out = np.fft.irfft(spec, n=n)
        return out / max(1e-9, np.max(np.abs(out)))
    rumble = bed(np.exp(-((f - 55) / 40) ** 2) + 0.4 * np.exp(-((f - 110) / 30) ** 2))
    hiss = bed(np.exp(-((f - 900) / 700) ** 2) * 0.5 + 0.2 * np.exp(-((f - 3000) / 1500) ** 2))
    # The boiler's throb: a slow beat, a whole number of beats to the loop
    throb = 0.75 + 0.25 * np.sin(2 * np.pi * t * 6 / 16.0)
    hum = 0.25 * np.sin(2 * np.pi * 50 * t) + 0.12 * np.sin(2 * np.pi * 100 * t)
    out = 0.9 * rumble * throb + 0.5 * hum * throb + 0.18 * hiss
    # Drips far off: soft, low-passed plinks with a long tail, wrapped round the loop's end
    for k in range(7):
        d = seconds(0.6)
        f0 = rng.uniform(700, 1300)
        drop = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 1.5 * np.minimum(d, 0.03) / 0.03)) / RATE) * np.exp(-d * 30)
        tail = np.zeros(int(1.2 * RATE))
        tail[: len(drop)] += drop
        for delay, gain in ((0.07, 0.4), (0.15, 0.25), (0.26, 0.15), (0.41, 0.08)):
            s = int(delay * RATE)
            tail[s: s + len(drop)] += gain * drop
        tail = band(tail, 300, 2500)
        at = int(rng.uniform(0, 16.0) * RATE)
        idx = (np.arange(len(tail)) + at) % n
        out[idx] += rng.uniform(0.12, 0.25) * tail
    out = 0.5 * out / max(1e-9, np.max(np.abs(out)))
    path = os.path.join(SOUNDS, "cellar.ogg")
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
