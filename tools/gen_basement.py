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
    detail_textures()
    link_textures()
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
    # (faint, joistsfaint: the same, giving off a faint light nobody can find the source of: Fandom's "every part of the
    # level is illuminated by a light which has no determined source")
    cube_block("basement-ceiling", ["plain", "stained", "joists", "faint", "joistsfaint", "shaft"], {
        "plain": alts("ceiling-plain", ["ceiling-plain-2"]),
        "stained": alts("ceiling-stained", ["ceiling-plain"]),
        "joists": alts("joists", ["joists-2"]),
        "faint": alts("ceiling-plain", ["ceiling-plain-2"]),
        "joistsfaint": alts("joists", ["joists-2"]),
        "shaft": alts("ceiling-plain", ["ceiling-plain-2"]),
    }, "The Basement: the low concrete ceiling (plain, drip-stained), bare joists under old floorboards (joists); faint, a ceiling with the light that has no source",
        # (Light leaving a block loses that block's absorption, so a ceiling that gives light must let it through: the
        # concrete over it stops it there, src/Worldgen/WorldLighting.cs)
        # (shaft, round 2: the broken slab lining a crack someone fell through, lit from the room above: it carries the
        # Lobby's yellow light down the twenty blocks to the floor, where it would otherwise never reach)
        {"lightHsvByType": {"*-faint": [8, 2, 6], "*-joistsfaint": [8, 2, 6], "*-shaft": [9, 3, 10]}, "lightAbsorption": 0})
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
    detail_blocks()
    link_blocks()
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
    detail_sounds()


# ======================================================================== Detail pass (2026-10-30)
#
# After the lore (docs/design/experimental-levels/lore/basement-brief.md): the Fandom basement's dusty carpet, wood
# panelling and wooden doors (basement-door, which opens and shuts: BackroomsBasementDoor in src/Regions/BasementSystem.cs),
# the brick of its Escherian stairwells, bare joists over its finished rooms; the crack in the ceiling someone fell
# through (the rubble under it, the frayed end of a rope high up in it); out-of-place things lying about (a coil of
# rope, a crowbar, an empty bottle, a jar gone bad) that can be picked up; and the elevator in the distance, dead
# (Level 5's cage lift in cinder block, no way through). Sounds: a baby crying behind a door, muffled; the lights of the
# Basement coming on.

LOBBY_CARPET = "backrooms:block/carpet-soaked"
BRASS = "backrooms:block/level5/brass"
ROT = {"north": 0, "east": 270, "south": 180, "west": 90}
WOOD_SOUNDS = {"walk": "game:walk/wood", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"}
STEP_BOXES = {
    "north": [{"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.5, "z2": 1}, {"x1": 0, "y1": 0.5, "z1": 0, "x2": 1, "y2": 1, "z2": 0.5}],
    "east": [{"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.5, "z2": 1}, {"x1": 0.5, "y1": 0.5, "z1": 0, "x2": 1, "y2": 1, "z2": 1}],
    "south": [{"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.5, "z2": 1}, {"x1": 0, "y1": 0.5, "z1": 0.5, "x2": 1, "y2": 1, "z2": 1}],
    "west": [{"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.5, "z2": 1}, {"x1": 0, "y1": 0.5, "z1": 0, "x2": 0.5, "y2": 1, "z2": 1}],
}


def carpet_tex(seed, base, tone2, wear):
    img = M.carpet(seed=seed, base=base, tone2=tone2, mix2=0.35, pile=9, grain=4, mottle=8, wear=wear)
    # Years of dust settled in the pile, and the odd dark stain
    M.grime(img, 0.22, seed=seed + 1, color=(112, 108, 96), cells=(8, 4, 2), cover=0.55)
    M.grime(img, 0.14, seed=seed + 2, color=(52, 46, 36), cells=(4, 2), cover=0.35)
    if seed % 2:
        at = M.spread(seed + 3, 1)[0]
        M.stain(img, seed=seed + 4, radius=8, color=(58, 50, 34), strength=0.4, at=at, ring=0.5)
    return img


def panel_tex(seed, stained=False):
    # Knotty pine panelling gone dark, the varnish dulled by dust; damp wicking up from below
    # (Round 2: darker and greyer than at first, which read as fresh orange pine under a torch)
    img = M.wood_planks(seed=seed, base=(100, 74, 50), planks=4, direction="v", grain=4, contrast=1.0, knots=1, flecks=0.8,
                        per_plank=8, gap=(36, 26, 18))
    M.grime(img, 0.26, seed=seed + 1, color=(78, 74, 64), cells=(8, 4), cover=0.6)
    if stained:
        M.tideline(img, 22, seed=seed + 2, color=(56, 44, 30), amount=0.45, wave=1.4, below=0.85)
        M.drips(img, n=2, seed=seed + 3, color=(62, 50, 34), length=(8, 20), strength=0.35, width=2)
    return img


def brick_tex(seed):
    img = M.brick(seed=1300, base=(116, 64, 48), mortar=(104, 98, 88), course=8, length=16, jitter=10, hue=4, pits=0.05,
                  grain=5, mottle=8, tones=seed)
    M.grime(img, 0.25, seed=seed + 1, color=(48, 44, 40), cells=(8, 4, 2), cover=0.5)
    M.grime(img, 0.12, seed=seed + 2, color=(150, 146, 132), cells=(4, 2), cover=0.25)  # efflorescence
    return img


def joists_tex(seed):
    # Looking up at the floor above: boards across, two dark joists along them, grey with cobweb and dust
    img = M.wood_planks(seed=seed, base=(96, 72, 48), planks=6, direction="h", grain=3, per_plank=8, gap=(30, 22, 16))
    for x0 in (6, 22):
        for y in range(32):
            for x in range(x0, x0 + 4):
                M.touch(img, x, y, -0.32 if x in (x0, x0 + 3) else -0.22)
    M.grime(img, 0.25, seed=seed + 1, color=(120, 118, 110), cells=(8, 4), cover=0.4)
    return img


def detail_textures():
    save(carpet_tex(201, (104, 102, 62), (88, 86, 54), 0.2), "carpet-olive")
    save(carpet_tex(202, (104, 102, 62), (88, 86, 54), 0.35), "carpet-olive-2")
    save(carpet_tex(203, (110, 84, 60), (94, 70, 50), 0.4), "carpet-brown")
    save(carpet_tex(204, (110, 84, 60), (94, 70, 50), 0.55), "carpet-brown-2")
    save(panel_tex(211), "panel")
    save(panel_tex(212), "panel-2")
    save(panel_tex(213, stained=True), "panel-stained")
    save(brick_tex(221), "brick")
    save(brick_tex(222), "brick-2")
    save(joists_tex(231), "joists")
    save(joists_tex(232), "joists-2")
    # The doors: old stained wood, scuffed; their frames painted once, a dull cream
    door = M.wood_planks(seed=241, base=(98, 64, 40), planks=3, direction="v", grain=3, per_plank=5, gap=(70, 46, 30), flecks=0.6)
    M.grime(door, 0.18, seed=242, color=(70, 60, 48), cells=(8, 4), cover=0.5)
    M.scratches(door, n=8, seed=243, length=(2, 6), light=0.18)
    save(door, "doorwood")
    frame = M.painted_metal(seed=244, base=(176, 166, 138), panel=False, chips=3, under=(110, 84, 60))
    M.grime(frame, 0.25, seed=245, color=(96, 88, 72), cells=(8, 4), cover=0.55)
    save(frame, "doorframe")
    # A rope's twist, a crowbar's chipped red paint over rust, green bottle glass, a jar's murky contents
    rope = M.fabric(seed=251, base=(150, 128, 92), weave="twill", contrast=16, grain=4, mottle=5)
    M.grime(rope, 0.2, seed=252, color=(90, 80, 60), cells=(4, 2), cover=0.5)
    save(rope, "rope")
    bar = M.painted_metal(seed=253, base=(128, 40, 32), panel=False, chips=6, under=(70, 56, 48))
    M.rust(bar, 0.35, seed=254, color=RUST, dark=RUSTDARK, cells=(4, 2))
    save(bar, "crowbar")
    glass = M.noise_hv((60, 88, 58), 4, seed=255, mottle=6)
    M.grime(glass, 0.3, seed=256, color=(40, 46, 34), cells=(4, 2), cover=0.5)
    save(glass, "bottle")
    jar = M.noise_hv((88, 78, 52), 5, seed=257, mottle=10)
    M.grime(jar, 0.4, seed=258, color=(46, 52, 30), cells=(8, 4, 2), cover=0.6)
    save(jar, "jar")
    # Round 2: a heating duct of galvanised sheet metal, dulled grey with dust, a rust bloom at its seams
    for k, seed in enumerate((261, 262)):
        duct = M.galvanised(seed=seed, base=(104, 108, 106), spangle=10, white_rust=0.08)
        M.grime(duct, 0.4, seed=seed + 10, color=(72, 70, 62), cells=(8, 4, 2), cover=0.7)
        M.emboss_lines(duct, xs=(0, 15, 16, 31), strength=0.18)
        M.rust(duct, 0.12, seed=seed + 20, color=RUST, dark=RUSTDARK, cells=(4, 2))
        save(duct, "duct" if k == 0 else "duct-2")


# ---- shapes ----

def kbox(name, frm, to, tex, faces=None, rot=None, origin=None):
    import modelkit as K
    return K.box(name, frm, to, tex, faces=faces or K.DIRS, rot=rot, origin=origin)


def write_shape(name, els, textures):
    keys = sorted({f["texture"][1:] for e in els for f in e["faces"].values()})
    table = {k: textures[k] for k in keys}
    write_json(os.path.join(SHAPES, name + ".json"), {"textureWidth": 16, "textureHeight": 16, "textures": table, "elements": els})
    return "block/basement/" + name


DOOR_TEX = {"doorwood": "backrooms:block/basement/doorwood", "doorframe": "backrooms:block/basement/doorframe", "brass": BRASS}


def door_frame():
    return [
        kbox("LiningW", (0, 0, 0), (1.25, 30.5, 16), "doorframe", faces=("east", "south", "north")),
        kbox("LiningE", (14.75, 0, 0), (16, 30.5, 16), "doorframe", faces=("west", "south", "north")),
        kbox("LiningHead", (0, 30.5, 0), (16, 32, 16), "doorframe", faces=("down", "south", "north")),
        kbox("CasingW", (-1.25, 0, -0.75), (1.25, 31.5, 0), "doorframe", faces=("north", "east", "west", "up")),
        kbox("CasingE", (14.75, 0, -0.75), (17.25, 31.5, 0), "doorframe", faces=("north", "east", "west", "up")),
        kbox("CasingHead", (1.25, 30.5, -0.75), (14.75, 32.75, 0), "doorframe", faces=("north", "down", "up")),
        kbox("InCasingW", (-1.25, 0, 16), (1.25, 31.5, 16.75), "doorframe", faces=("south", "east", "west", "up")),
        kbox("InCasingE", (14.75, 0, 16), (17.25, 31.5, 16.75), "doorframe", faces=("south", "east", "west", "up")),
        kbox("InCasingHead", (1.25, 30.5, 16), (14.75, 32.75, 16.75), "doorframe", faces=("south", "down", "up")),
    ]


def door_leaf():
    """The leaf, shut, hinged at its west edge: four panels, a brass knob on either face at its east edge, two hinges."""
    import modelkit as K
    x1, x2, y1, y2, z1, z2 = 1.35, 14.65, 0.4, 30.4, 2.0, 3.75
    els = K.frame_and_panel("Leaf", (x1, y1, z1), (x2, y2, z2), "doorwood", border=2.0, depth=0.5, grid=(2, 2), raised=0.5)
    for f, (za, zb, zc, zd) in (("O", (z1 - 0.5, z1, z1 - 2.0, z1 - 0.5)), ("I", (z2, z2 + 0.5, z2 + 0.5, z2 + 2.0))):
        els += [kbox(f"Rose{f}", (12.0, 14.5, za), (13.5, 16.0, zb), "brass"), kbox(f"Knob{f}", (12.25, 14.75, zc), (13.25, 15.75, zd), "brass")]
    for k, y in enumerate((3.0, 26.0)):
        els.append(kbox(f"Hinge{k}", (1.35, y, z2), (2.35, y + 2.5, z2 + 0.25), "brass", faces=("south", "east", "up", "down")))
    return els


def door_open(leaf):
    import modelkit as K
    return K.move(K.turn(leaf, 1), dx=1.35 + 0.5 - 12.25, dz=3.75 - 1.35)


def cuboid(b, side=None):
    x1, y1, z1, x2, y2, z2 = b
    c = {"x1": x1, "y1": y1, "z1": z1, "x2": x2, "y2": y2, "z2": z2}
    if side and ROT[side]:
        c["rotateY"] = ROT[side]
    return c


def door_blocks():
    from gen_suburbs import cut, mirror_x
    shape_by, coll_by = {}, {}
    closed = door_frame() + door_leaf()
    opened = door_frame() + door_open(door_leaf())
    for state, els in (("closed", closed), ("open", opened)):
        for hinge in ("w", "e"):
            model = els if hinge == "w" else mirror_x(els)
            parts = cut(model, 1, 2)
            for r, half in enumerate(("lower", "upper")):
                path = write_shape(f"door-{state}-{hinge}{half}", parts[(0, r)], DOOR_TEX)
                for st in ((state, "jammed") if state == "closed" else (state,)):
                    for side, rot in ROT.items():
                        shape_by[f"*-{st}-{hinge}-{half}-{side}"] = {"base": path, "rotateY": rot}
    for st in ("closed", "open", "jammed"):
        for hinge in ("w", "e"):
            b = (0, 0, 2 / 16, 1, 1, 3.75 / 16) if st != "open" else (1.35 / 16, 0, 3.75 / 16, 4 / 16, 1, 1)
            if hinge == "e":
                b = (1 - b[3], b[1], b[2], 1 - b[0], b[4], b[5])
            for side in ROT:
                coll_by[f"*-{st}-{hinge}-*-{side}"] = [cuboid(b, side)]
    write_json(os.path.join(BLOCKS, "basement-door.json"), {
        "code": "basement-door",
        "variantgroups": [{"code": "state", "states": ["closed", "open", "jammed"]}, {"code": "hinge", "states": ["w", "e"]},
                          {"code": "part", "states": ["lower", "upper"]}, {"code": "side", "states": list(ROT)}],
        "creativeinventory": {"general": ["*-closed-w-lower-north"], "construction": ["*-closed-w-lower-north"]},
        "behaviors": [{"name": "BackroomsBasementDoor"}],
        "blockmaterial": "Wood", "drawtype": "json", "shapeByType": shape_by, "collisionSelectionBoxesByType": coll_by,
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 1, "resistance": 3, "drops": [],
        "sounds": WOOD_SOUNDS,
    }, "The Basement: an old wooden door (closed, open, or swollen shut in its frame); right-click opens or shuts it")


def debris_model(kind):
    """Under the crack: broken floorboards and a torn scrap of the yellow carpet from above, or chunks of the slab."""
    if kind == "boards":
        return [
            kbox("Board1", (1, 0, 6), (15, 1, 9), "panel", rot=(0, 22.5, 0)),
            kbox("Board2", (3, 1, 3), (13, 2, 5.5), "panel", rot=(0, -22.5, 0)),
            kbox("Board3", (5, 0, 11), (14, 1.5, 13.5), "panel"),
            kbox("Carpet", (2, 0.1, 1), (11, 0.6, 9), "lobby", rot=(0, 22.5, 0)),
            kbox("Chunk", (10, 0, 2), (13, 2.5, 5), "concrete", rot=(0, 45, 0)),
        ]
    return [
        kbox("Chunk1", (2, 0, 3), (7, 3, 8), "concrete", rot=(0, 22.5, 0)),
        kbox("Chunk2", (8, 0, 7), (14, 2, 12), "concrete", rot=(0, -22.5, 0)),
        kbox("Chunk3", (4, 0, 10), (7, 1.5, 13), "concrete", rot=(0, 45, 0)),
        kbox("Carpet", (6, 0.1, 1), (14, 0.6, 6), "lobby", rot=(0, -22.5, 0)),
        kbox("Board", (1, 0, 12), (12, 1, 14.5), "panel"),
    ]


def junk_model(kind):
    if kind == "rope":  # a coil of rope, its tail run out across the floor
        els = []
        for k, r in enumerate((4.5, 3.5)):
            y = k * 1.0
            els += [kbox(f"N{k}", (8 - r, y, 8 - r), (8 + r, y + 1, 9 - r), "rope"), kbox(f"S{k}", (8 - r, y, 7 + r), (8 + r, y + 1, 8 + r), "rope"),
                    kbox(f"W{k}", (8 - r, y, 9 - r), (9 - r, y + 1, 7 + r), "rope"), kbox(f"E{k}", (7 + r, y, 9 - r), (8 + r, y + 1, 7 + r), "rope")]
        els.append(kbox("Tail", (11, 0, 12), (12, 0.75, 16), "rope", rot=(0, 22.5, 0)))
        return els
    if kind == "crowbar":  # an old crowbar, its hooked claw at one end
        o = (8, 0.5, 8)
        return [kbox("Bar", (7.5, 0, 1.5), (8.5, 1, 13.5), "crowbar", rot=(0, 22.5, 0), origin=o),
                kbox("Claw", (7.5, 0, 13.5), (8.5, 2.5, 14.5), "crowbar", rot=(0, 22.5, 0), origin=o),
                kbox("Hook", (7.5, 2.5, 11.5), (8.5, 3.5, 14.5), "crowbar", rot=(0, 22.5, 0), origin=o)]
    if kind == "bottle":  # an empty bottle on its side
        o = (8, 1.5, 8)
        return [kbox("Body", (6.5, 0, 4), (9.5, 3, 11), "bottle", rot=(0, -22.5, 0), origin=o),
                kbox("Neck", (7.25, 0.75, 11), (8.75, 2.25, 14), "bottle", rot=(0, -22.5, 0), origin=o)]
    return [kbox("Jar", (5.5, 0, 5.5), (10.5, 6, 10.5), "jar"), kbox("Lid", (5.25, 6, 5.25), (10.75, 7, 10.75), "lid")]


JUNK = {  # kind: what it gives when broken
    "rope": [{"type": "item", "code": "game:rope", "quantity": {"avg": 1, "var": 0}}],
    "crowbar": [{"type": "item", "code": "prybar", "quantity": {"avg": 1, "var": 0}}],
    "bottle": [{"type": "item", "code": "emptybottle", "quantity": {"avg": 1, "var": 0}}],
    "jar": [{"type": "item", "code": "game:rot", "quantity": {"avg": 2, "var": 1}}],
}


def rope_model(part):
    """The frayed end of a rope hanging in the crack, out of reach: a strand the whole block (hang), or its end, unravelling."""
    if part == "hang":
        return [kbox("Strand", (7.5, 0, 7.5), (8.5, 16, 8.5), "rope")]
    return [kbox("Strand", (7.5, 6, 7.5), (8.5, 16, 8.5), "rope"),
            kbox("Fray1", (7, 2, 7.5), (7.5, 6.5, 8), "rope", rot=(0, 0, 22.5)),
            kbox("Fray2", (8.5, 3, 8), (9, 6.5, 8.5), "rope", rot=(0, 0, -22.5)),
            kbox("Fray3", (7.75, 1, 8.5), (8.25, 6, 9), "rope", rot=(22.5, 0, 0))]


def duct_model():
    """A rectangular heating duct along the top of the block (west to east), hung from the joists on a strap, a seam
    flange at the joint."""
    return [kbox("Duct", (0, 6.5, 2.5), (16, 14.5, 13.5), "duct", faces=("north", "south", "up", "down")),
            kbox("Flange", (0, 6.2, 2.2), (1, 14.8, 13.8), "duct"),
            kbox("StrapN", (9, 6, 2), (10, 16, 2.4), "duct"),
            kbox("StrapS", (9, 6, 13.6), (10, 16, 14), "duct"),
            kbox("StrapB", (9, 6, 2), (10, 6.4, 14), "duct")]


def detail_blocks():
    cube_block("basement-carpet", ["olive", "brown"], {
        "olive": alts("carpet-olive", ["carpet-olive-2"], rotate=True),
        "brown": alts("carpet-brown", ["carpet-brown-2"], rotate=True),
    }, "The Basement: dusty carpet laid over the concrete (olive shag, worn brown)",
        {"blockmaterial": "Cloth", "resistance": 2, "requiredMiningTier": 0,
         "sounds": {"walk": "game:walk/cloth", "place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"},
         "drops": [{"type": "item", "code": "carpetfibre", "quantity": {"avg": 1.5, "var": 1}}]})
    cube_block("basement-panel", ["plain", "stained"], {
        "plain": alts("panel", ["panel-2"]),
        "stained": alts("panel-stained", ["panel"]),
    }, "The Basement: old knotty pine panelling over the block walls (plain; stained by the damp)",
        {"blockmaterial": "Wood", "resistance": 3, "requiredMiningTier": 0, "sounds": WOOD_SOUNDS,
         "drops": [{"type": "item", "code": "game:stick", "quantity": {"avg": 1, "var": 1}}]})
    cube_block("basement-brick", ["plain"], {"plain": alts("brick", ["brick-2"])},
               "The Basement: the old brick of a stairwell that goes up and down to the same floor")
    write_json(os.path.join(BLOCKS, "basement-bricksteps.json"), {
        "code": "basement-bricksteps",
        "variantgroups": [{"code": "side", "states": list(ROT)}],
        "creativeinventory": {"general": ["*-north"], "construction": ["*-north"]},
        "blockmaterial": "Stone", "drawtype": "json",
        "shapeByType": {f"*-{s}": {"base": "block/concretestairs", "rotateY": r} for s, r in ROT.items()},
        "textures": {"concrete": {"base": "block/basement/brick"}},
        "collisionSelectionBoxesByType": {f"*-{s}": b for s, b in STEP_BOXES.items()},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0,
        "resistance": 8, "requiredMiningTier": 3, "sounds": STONE_SOUNDS,
    }, "The Basement: a brick step of an Escherian stairwell; the variant is the way it climbs")

    door_blocks()

    tex = {"panel": "backrooms:block/basement/panel", "lobby": LOBBY_CARPET, "concrete": "backrooms:block/basement/floor-dry",
           "rope": "backrooms:block/basement/rope", "crowbar": "backrooms:block/basement/crowbar", "bottle": "backrooms:block/basement/bottle",
           "jar": "backrooms:block/basement/jar", "lid": "backrooms:block/basement/cage"}
    for kind in ("boards", "chunks"):
        write_shape(f"debris-{kind}", debris_model(kind), tex)
    write_json(os.path.join(BLOCKS, "basement-debris.json"), {
        "code": "basement-debris",
        "variantgroups": [{"code": "kind", "states": ["boards", "chunks"]}, {"code": "side", "states": list(ROT)}],
        "creativeinventory": {"general": ["*-north"], "decorative": ["*-north"]},
        "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": {f"*-{k}-{s}": {"base": f"block/basement/debris-{k}", "rotateY": r} for k in ("boards", "chunks") for s, r in ROT.items()},
        "collisionbox": None, "selectionbox": {"x1": 0.05, "y1": 0, "z1": 0.05, "x2": 0.95, "y2": 0.2, "z2": 0.95},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 1, "replaceable": 400,
        "drops": [{"type": "item", "code": "game:stick", "quantity": {"avg": 1, "var": 1}},
                  {"type": "item", "code": "carpetfibre", "quantity": {"avg": 0.5, "var": 0.5}}],
        "sounds": WOOD_SOUNDS,
    }, "The Basement: what came down with whoever broke through the floor above (boards and carpet, or chunks of the slab)")

    for kind in JUNK:
        write_shape(f"junk-{kind}", junk_model(kind), tex)
    write_json(os.path.join(BLOCKS, "basement-junk.json"), {
        "code": "basement-junk",
        "variantgroups": [{"code": "kind", "states": list(JUNK)}, {"code": "side", "states": list(ROT)}],
        "creativeinventory": {"general": ["*-north"], "decorative": ["*-north"]},
        "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": {f"*-{k}-{s}": {"base": f"block/basement/junk-{k}", "rotateY": r} for k in JUNK for s, r in ROT.items()},
        "collisionbox": None, "selectionbox": {"x1": 0.2, "y1": 0, "z1": 0.2, "x2": 0.8, "y2": 0.4, "z2": 0.8},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 0.3, "replaceable": 400,
        "dropsByType": {f"*-{k}-*": d for k, d in JUNK.items()},
        "sounds": {"place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"},
    }, "The Basement: things lying where somebody left them: a coil of rope, an old crowbar, an empty bottle, a jar gone bad")

    for part in ("hang", "end"):
        write_shape(f"rope-{part}", rope_model(part), tex)
    write_json(os.path.join(BLOCKS, "basement-rope.json"), {
        "code": "basement-rope",
        "variantgroups": [{"code": "part", "states": ["hang", "end"]}],
        "creativeinventory": {"general": ["*-end"], "decorative": ["*-end"]},
        "blockmaterial": "Cloth", "drawtype": "json",
        "shapeByType": {f"*-{p}": {"base": f"block/basement/rope-{p}"} for p in ("hang", "end")},
        "collisionbox": None, "selectionbox": {"x1": 0.4, "y1": 0, "z1": 0.4, "x2": 0.6, "y2": 1, "z2": 0.6},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 0.5, "drops": [],
        "sounds": {"place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"},
    }, "The Basement: the frayed end of a rope hanging high in the crack, cut or worn through")

    # Round 2: the heating duct under the ceiling
    write_shape("duct", duct_model(), {"duct": "backrooms:block/basement/duct"})
    write_json(os.path.join(BLOCKS, "basement-duct.json"), {
        "code": "basement-duct",
        "variantgroups": [{"code": "axis", "states": ["we", "ns"]}],
        "creativeinventory": {"general": ["*-we"], "decorative": ["*-we"]},
        "blockmaterial": "Metal", "drawtype": "json",
        "shapeByType": {"*-we": {"base": "block/basement/duct"}, "*-ns": {"base": "block/basement/duct", "rotateY": 90}},
        "texturesByType": {"*": {"duct": {"base": "block/basement/duct", "alternates": [{"base": "block/basement/duct-2"}]}}},
        "collisionboxByType": {"*-we": {"x1": 0, "y1": 0.375, "z1": 0.125, "x2": 1, "y2": 1, "z2": 0.875},
                               "*-ns": {"x1": 0.125, "y1": 0.375, "z1": 0, "x2": 0.875, "y2": 1, "z2": 1}},
        "selectionboxByType": {"*-we": {"x1": 0, "y1": 0.375, "z1": 0.125, "x2": 1, "y2": 1, "z2": 0.875},
                               "*-ns": {"x1": 0.125, "y1": 0.375, "z1": 0, "x2": 0.875, "y2": 1, "z2": 1}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 2,
        "drops": [{"type": "item", "code": "metalbracket", "quantity": {"avg": 0.5, "var": 0.5}}],
        "sounds": {"place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"},
    }, "The Basement: a heating duct of galvanised sheet metal under the ceiling, grey with dust")

    # The elevator in the distance: Level 5's cage lift set in the Basement's cinder block, dead (no way through)
    lift_shape = {}
    for part in ("lower", "upper", "dial"):
        for half in ("l", "r"):
            for side, r in ROT.items():
                lift_shape[f"*-{part}-{half}-{side}"] = {"base": f"block/detail/cagelift-plaster-{part}-{half}", "rotateY": r}
    write_json(os.path.join(BLOCKS, "basement-lift.json"), {
        "code": "basement-lift",
        "variantgroups": [{"code": "part", "states": ["lower", "upper", "dial"]}, {"code": "half", "states": ["l", "r"]},
                          {"code": "side", "states": list(ROT)}],
        "creativeinventory": {"general": ["*-lower-l-north"], "decorative": ["*-lower-l-north"]},
        "blockmaterial": "Metal", "drawtype": "json", "shapeByType": lift_shape,
        "textures": {"plaster": {"base": "block/basement/wall-plain"}},
        "lightAbsorption": 99, "resistance": 4, "drops": [],
        "sounds": {"walk": "game:walk/stone", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"},
    }, "The Basement: an old cage elevator, dead: the gate will not move and nothing answers the button")


def detail_sounds():
    """Behind a shut door, a baby crying, muffled (a loop of 10 s: bursts of crying, breaths between); and the lights of
    the Basement coming on all at once (a relay's clunk, then the hum swelling)."""
    from gen_entity_sounds import RATE, band
    from oggutil import write_ogg
    rng = np.random.default_rng(2202)
    n = int(10.0 * RATE)
    out = np.zeros(n)
    at = 0.3
    while at < 9.0:
        dur = rng.uniform(0.7, 1.4)
        m = int(dur * RATE)
        tt = np.arange(m) / RATE
        # The cry's pitch: up fast, a wobble, down at the end (an infant's 400-550 Hz)
        f0 = rng.uniform(420, 520) * (1 + 0.18 * np.sin(np.pi * np.minimum(tt / dur, 1)) - 0.12 * (tt / dur) ** 3)
        f0 *= 1 + 0.02 * np.sin(2 * np.pi * rng.uniform(5, 7) * tt)
        phase = 2 * np.pi * np.cumsum(f0) / RATE
        voice = sum((1.0 / k) * np.sin(k * phase) for k in range(1, 9))
        # The open "waa": its harmonics near 1.1, 2.0 and 3.4 kHz brought up
        voice = band(voice, 700, 1500) + band(voice, 1700, 2400) * 0.6 + band(voice, 3000, 3800) * 0.25
        env = np.minimum(1, tt / 0.06) * np.minimum(1, (dur - tt) / 0.15) * (0.7 + 0.3 * np.sin(np.pi * tt / dur))
        breath = band(rng.normal(size=m), 500, 2500) * 0.08
        seg = (voice + breath) * env
        s = int(at * RATE)
        e = min(n, s + m)
        out[s:e] += seg[: e - s]
        at += dur + rng.uniform(0.35, 0.9)
    # Through a door and a room: only the low part of it gets through, with the room's echo
    out = band(out, 120, 900)
    wet = np.zeros_like(out)
    for delay, gain in ((0.031, 0.5), (0.057, 0.35), (0.093, 0.25), (0.141, 0.15)):
        d = int(delay * RATE)
        wet[d:] += gain * out[:-d]
    out = out + wet
    out = 0.45 * out / max(1e-9, np.max(np.abs(out)))
    path = os.path.join(SOUNDS, "cry.ogg")
    if write_ogg(path, out, RATE):
        print("wrote", os.path.relpath(path, ROOT))

    # The lights coming on: a heavy relay's clunk somewhere, then every bulb's hum swelling up together
    n = int(3.0 * RATE)
    t = np.arange(n) / RATE
    clunk = band(rng.normal(size=n), 60, 900) * np.exp(-t * 28) * 1.4
    clunk += np.sin(2 * np.pi * 70 * t) * np.exp(-t * 18) * 0.9
    swell = np.minimum(1, np.maximum(0, (t - 0.12) / 1.2))
    hum = (0.5 * np.sin(2 * np.pi * 60 * t) + 0.3 * np.sin(2 * np.pi * 120 * t) + 0.12 * np.sin(2 * np.pi * 180 * t)) * swell
    hum *= np.minimum(1, (3.0 - t) / 1.0)
    tick = np.zeros(n)
    for k in range(5):
        s = int(rng.uniform(0.15, 0.6) * RATE)
        m = int(0.02 * RATE)
        tick[s:s + m] += band(rng.normal(size=m), 1500, 5000) * 0.5
    out = clunk + 0.5 * hum + tick
    out = 0.6 * out / max(1e-9, np.max(np.abs(out)))
    path = os.path.join(SOUNDS, "lightson.ogg")
    if write_ogg(path, out, RATE):
        print("wrote", os.path.relpath(path, ROOT))


# ======================================================================== Links (2026-10-31)
#
# The way in, in other levels (docs/design/experimental-levels/LINKS.md; src/Worldgen/WorldLayout.LevelBasement.Links.cs):
# "breaking through the floor of most levels" (Fandom). A patch of cracked floor five by five in Level 0, 1, 2, 4 or 5,
# drawn over the host's own floor as a flat decal one piece a tile (basement-floorcrack): in its middle the floor broken
# through to the dark under it and sagging round the hole, cracks running out from it, rings of fracture round it, and
# hairline cracks over the edge. Dark only, so it reads on yellow carpet, office carpet, hotel rugs and bare concrete
# alike. Two drawings (a, b), each also turned half about by the generator (variant s).

CRACK_TILE = 32
CRACK_INK = (18, 14, 10)
CRACK_LIP = (226, 216, 196)


def crack_pattern(seed):
    """One drawing of a cracked patch, five tiles by five, as RGBA (drawn four times over and scaled down, for clean lines)."""
    import math
    import random
    from PIL import Image, ImageDraw, ImageFilter
    rng = random.Random(seed)
    k = 4
    n = 5 * CRACK_TILE * k
    c = n / 2 + rng.uniform(-3, 3) * k
    cz = n / 2 + rng.uniform(-3, 3) * k
    unit = CRACK_TILE * k  # one tile
    ink = Image.new("L", (n, n), 0)      # the dark of the cracks and the hole
    lit = Image.new("L", (n, n), 0)      # a pale broken edge along one side of the big cracks
    d, dl = ImageDraw.Draw(ink), ImageDraw.Draw(lit)

    # The sag: the middle three by three darkens toward the hole, as if the floor had settled into it
    sag = Image.new("L", (n, n), 0)
    sd = ImageDraw.Draw(sag)
    steps = 40
    for i in range(steps):
        r = 1.6 * unit * (1 - i / steps)
        sd.ellipse([c - r, cz - r, c + r, cz + r], fill=int(130 * (i / steps) ** 1.3))
    sag = sag.filter(ImageFilter.GaussianBlur(7 * k))

    # The hole: a jagged ring of broken edge round the dark, a pale lip on its far side
    pts = []
    m = 13
    base = rng.uniform(0.5, 0.6) * unit
    for i in range(m):
        a = 2 * math.pi * i / m + rng.uniform(-0.15, 0.15)
        r = base * rng.uniform(0.72, 1.25)
        pts.append((c + r * math.cos(a), cz + r * math.sin(a)))
    dl.polygon([(x + 1.5 * k, y + 1.5 * k) for x, y in pts], fill=70)
    d.polygon(pts, fill=246)

    def walk(x, y, ang, length, width, a0, branch, edge):
        """A crack: straight runs with sharp kinks, thinning as it goes, now and then forking."""
        done = 0.0
        while done < length:
            seg = rng.uniform(5, 11) * k
            ang += rng.uniform(-0.55, 0.55) if rng.random() < 0.4 else rng.uniform(-0.12, 0.12)
            nx, ny = x + seg * math.cos(ang), y + seg * math.sin(ang)
            t = done / length
            w = max(k * 0.8, width * (1 - 0.7 * t))
            if edge and w > 1.6 * k:
                ox, oy = -math.sin(ang) * w * 0.6, math.cos(ang) * w * 0.6
                dl.line([(x + ox, y + oy), (nx + ox, ny + oy)], fill=int(60 * (1 - t)), width=int(round(w * 0.6)))
            d.line([(x, y), (nx, ny)], fill=int(a0 * (1 - 0.4 * t)), width=int(round(w)))
            if branch and rng.random() < 0.12 and t < 0.75:
                walk(nx, ny, ang + rng.choice((-1, 1)) * rng.uniform(0.45, 1.0), (length - done) * rng.uniform(0.3, 0.55), w * 0.6, a0 * 0.85, False, False)
            x, y = nx, ny
            done += seg

    # The main cracks, out from the hole across the middle and on into the edge
    spokes = rng.randint(7, 9)
    angles = sorted(2 * math.pi * i / spokes + rng.uniform(-0.25, 0.25) for i in range(spokes))
    for a in angles:
        r0 = base * 0.85
        walk(c + r0 * math.cos(a), cz + r0 * math.sin(a), a, rng.uniform(1.15, 1.95) * unit, 2.6 * k, 230, True, True)

    # Rings of fracture between the spokes: the plates the floor broke into round the hole (angular, a few corners each)
    for ring, (rr, p) in enumerate(((0.9, 0.85), (1.4, 0.5))):
        for i in range(spokes):
            if rng.random() > p:
                continue
            a0, a1 = angles[i], angles[(i + 1) % spokes] + (2 * math.pi if i + 1 == spokes else 0)
            line = []
            corners = rng.randint(3, 4)
            for j in range(corners + 1):
                a = a0 + (a1 - a0) * j / corners
                r = rr * unit * rng.uniform(0.88, 1.12)
                line.append((c + r * math.cos(a), cz + r * math.sin(a)))
            d.line(line, fill=200 if ring == 0 else 165, width=int(round((1.7 if ring == 0 else 1.2) * k)))

    # Hairline cracks over the edge, faint
    for _ in range(rng.randint(10, 14)):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(1.35, 1.9) * unit
        walk(c + r * math.cos(a), cz + r * math.sin(a), a + rng.uniform(-0.8, 0.8), rng.uniform(0.3, 0.6) * unit, 0.9 * k, 125, False, False)

    ink_a = np.maximum(np.asarray(ink), np.asarray(sag)).astype(np.float64) / 255
    lit_a = np.asarray(lit).astype(np.float64) / 255 * (1 - ink_a)
    alpha = ink_a + lit_a
    rgb = np.zeros((n, n, 3))
    for ch in range(3):
        rgb[..., ch] = (CRACK_INK[ch] * ink_a + CRACK_LIP[ch] * lit_a) / np.maximum(alpha, 1e-6)
    out = Image.fromarray(np.dstack([rgb, alpha * 255]).clip(0, 255).astype(np.uint8), "RGBA")
    out = out.resize((5 * CRACK_TILE, 5 * CRACK_TILE), Image.LANCZOS)
    # (Nothing may reach the patch's outer edge: the floor round it is whole)
    a = np.asarray(out).copy()
    edge = 3
    a[:edge, :, 3] = 0
    a[-edge:, :, 3] = 0
    a[:, :edge, 3] = 0
    a[:, -edge:, 3] = 0
    return Image.fromarray(a, "RGBA")


def link_textures():
    for name, seed in (("a", 901), ("b", 902)):
        img = crack_pattern(seed)
        for r in range(5):
            for col in range(5):
                piece = img.crop((col * CRACK_TILE, r * CRACK_TILE, (col + 1) * CRACK_TILE, (r + 1) * CRACK_TILE))
                save(piece, f"floorcrack-{name}-p{r}{col}")


def link_blocks():
    # A flat decal lying on the floor, its one face up (a hair over the floor, so it never fights it)
    write_json(os.path.join(SHAPES, "floorcrack.json"), {
        "textureWidth": 16, "textureHeight": 16, "textures": {"crack": "backrooms:block/basement/floorcrack-a-p22"},
        "elements": [{"name": "Crack", "from": [0, 0.2, 0], "to": [16, 0.2, 16],
                      "faces": {"up": {"texture": "#crack", "uv": [0, 0, 16, 16]}}}]})
    parts = [f"p{r}{c}" for r in range(5) for c in range(5)]
    write_json(os.path.join(BLOCKS, "basement-floorcrack.json"), {
        "code": "basement-floorcrack",
        "variantgroups": [{"code": "drawing", "states": ["a", "b"]}, {"code": "part", "states": parts},
                          {"code": "turn", "states": ["n", "s"]}],
        "creativeinventory": {"general": ["*-a-p22-n"], "decorative": ["*-a-p22-n"]},
        "blockmaterial": "Stone", "drawtype": "json", "renderpass": "Transparent",
        "shapeByType": {"*-n": {"base": "block/basement/floorcrack"}, "*-s": {"base": "block/basement/floorcrack", "rotateY": 180}},
        "texturesByType": {f"*-{dr}-{p}-*": {"crack": {"base": f"block/basement/floorcrack-{dr}-{p}"}} for dr in ("a", "b") for p in parts},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0,
        "collisionbox": None,
        "selectionbox": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.05, "z2": 1},
        "resistance": 1, "drops": [],
        "sounds": {"place": "game:block/loosestone", "break": "game:block/loosestone", "hit": "game:block/loosestone"},
    }, "The Basement's way in, in other levels: a piece of a patch of cracked floor, five by five, that gives way in its middle "
       "(drawing a or b, part p<row><column>, turned: n as drawn, s half about)")


if __name__ == "__main__":
    what = set(sys.argv[1:]) or {"tex", "blocks", "sounds"}
    if "tex" in what:
        textures()
    if "blocks" in what:
        blocks()
    if "sounds" in what:
        sounds()
