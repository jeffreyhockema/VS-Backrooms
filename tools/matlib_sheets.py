"""Evidence sheets for tools/matlib.py: every surface family in a few parameterisations beside its closest vanilla
textures, plain and as 3x3 repeats, plus the operations, the ceiling module and a seam check.

    python tools/matlib_sheets.py [--out review/b2] [family ...]

Writes <out>/tex/<family>/*.png (the samples), <out>/<family>.png and <out>/<family>-tile.png (texsheet.py sheets,
vanilla references framed in gold in the first row), and prints a seam score per sample (see seam_score): about 1 or under
is seamless; a texture whose own structure sits on its edge (a panel seam, the T-bar) scores higher by design and is
marked so.
Nothing under assets/ is touched. A level batch can add its own parameterisations to FAMILIES to judge them.
"""
import argparse
import os
import sys
from types import SimpleNamespace

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matlib as M  # noqa: E402
import texsheet  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def _chevron_motif(w=32, h=32):
    """Level 0's chevron columns as a dye pattern (for the paper sample only; B3 owns the real one)."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    p = im.load()
    for col in range(w // 8):
        x0, off = col * 8, (col % 2) * 4
        for y in range(h):
            if (y // 2) % 2 == 0:
                p[x0 + 4, y] = (236, 230, 196, 255)
            row = (y + off) % 8
            for dx, r in ((4, 0), (3, 1), (5, 1), (2, 2), (6, 2)):
                if row == r:
                    p[x0 + dx, y] = (176, 170, 118, 255)
    return im


def _rug_motif(w=32, h=32):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    p = im.load()
    for y in range(h):
        for x in range(w):
            u, v = (x % 16) - 7.5, (y % 16) - 7.5
            if abs(abs(u) + abs(v) - 6) < 1.0:
                p[x, y] = (196, 150, 84, 255)
            elif abs(u) + abs(v) < 2:
                p[x, y] = (70, 30, 34, 255)
    return im


def _ops():
    base = lambda s=1: M.plaster(seed=s, base=(196, 192, 182))
    metal = lambda s=2: M.painted_metal(seed=s, base=(104, 122, 118), panel=False, chips=0)
    out = []
    out.append(("noise_hv", M.noise_hv((150, 140, 120), 4, 5)))
    out.append(("ao_border", M.ao_border(base(), 3, 0.3)))
    out.append(("bevel", M.bevel(base(), (4, 4, 28, 28), 2, 0.2)))
    out.append(("inset", M.inset(base(), (4, 4, 28, 28), 2, 0.25)))
    out.append(("hue_jitter", M.hue_jitter(M.noise_hv((150, 150, 150), 3, 3, mottle=3, hue=0), 8, 3, 8)))
    out.append(("grime-bottom", M.grime(base(), 0.25, 4, bias="bottom", cover=0.8)))
    out.append(("scratches", M.scratches(metal(), 10, 5)))
    out.append(("drips", M.drips(base(), 4, 6, start=0)))
    out.append(("rust", M.rust(metal(), 0.3, 7)))
    out.append(("rust-edges", M.rust(metal(), 0.15, 8, edges=True)))
    out.append(("chip_edges", M.chip_edges(metal(), (2, 2, 30, 30), 9, 8)))
    out.append(("emboss-groove", M.emboss_lines(base(), ys=(10, 21), xs=(15,))))
    out.append(("emboss-rib", M.emboss_lines(base(), ys=(10, 21), raised=True)))
    out.append(("stain", M.stain(base(), 10, radius=10)))
    out.append(("tideline", M.tideline(base(), 18, 11)))
    out.append(("multiply", M.multiply(base(), _rug_motif(), 0.5)))
    return out


def _alternates():
    fn = lambda s, at: M.stain(M.concrete(seed=s, cracks=0), s, radius=8, at=at, color=(96, 84, 64), strength=0.3)
    alts = M.alternates(fn, 40, 2)
    plain = [M.concrete(seed=s, cracks=0) for s in (41, 42, 43, 44)]
    out = [(f"stain-alt{k}", im) for k, im in enumerate(alts)] + [(f"plain-alt{k}", im) for k, im in enumerate(plain[:2])]
    # a 6x6 floor of random alternates, as the game picks them: the stain in one block in three, never in one place
    import random
    rng = random.Random(1)
    pool = alts + plain
    mix = Image.new("RGBA", (192, 192))
    for j in range(6):
        for i in range(6):
            mix.paste(rng.choice(pool), (i * 32, j * 32))
    out.append(("floor-mix-6x6", mix))
    return out


FAMILIES = {
    "noise": (["block/stone/plaster/plain", "block/metal/plate/iron"], lambda: [
        ("noise_fill-old", __import__("gen_textures").noise_fill((150, 140, 120), 6, 5)),
        ("noise_hv-default", M.noise_hv((150, 140, 120), 4, 5)),
        ("noise_hv-grey", M.noise_hv((128, 128, 128), 4, 6, mottle=8)),
        ("noise_hv-flat", M.noise_hv((150, 140, 120), 3, 7, mottle=3, hue=1)),
    ]),
    "concrete": (["block/stone/polishedrock/andesite", "block/stone/cobblestone/granite1"], lambda: [
        ("plain", M.concrete(seed=1)),
        ("floor-swirl", M.concrete(seed=2, base=(124, 122, 116), swirl=1, aggregate=0.09)),
        ("floor-swirl-alt-crack", M.concrete(seed=6, base=(124, 122, 116), swirl=1, cracks=1, aggregate=0.09)),
        ("formboard-wall", M.concrete(seed=3, base=(138, 136, 128), joints=(15,), cracks=0)),
        ("tunnel-dark", M.concrete(seed=4, base=(86, 84, 80), aggregate=0.1, pores=0.02, mottle=9)),
        ("slab-border", M.concrete(seed=5, base=(150, 146, 136), border=3)),
    ]),
    "plaster": (["block/stone/plaster/plain"], lambda: [
        ("white", M.plaster(seed=1)),
        ("office-grey", M.plaster(seed=2, base=(184, 180, 170), roller=0.8)),
        ("warm-cream", M.plaster(seed=3, base=(220, 204, 170), mottle=8)),
        ("teal-paint", M.plaster(seed=4, base=(120, 150, 144), roller=0.6, bumps=0.02)),
    ]),
    "paper": (["block/wallpaper/normal/yellow", "block/wallpaper/aged/walnut"], lambda: [
        ("plain-seams16", M.paper(seed=1)),
        ("chevron-dyed", M.dye(M.paper(seed=2, base=(214, 210, 140)), _chevron_motif(), (214, 210, 140))),
        ("manila-noseam", M.paper(seed=3, base=(212, 190, 138), seams=None, fibre=0.9)),
        ("red-tideline", M.tideline(M.paper(seed=4, base=(138, 44, 36), seams=32), 22, 4, color=(84, 30, 24), amount=0.35)),
    ]),
    "painted_metal": (["block/metal/sheet-plain/steel1", "block/metal/plate/iron"], lambda: [
        ("panel-green", M.painted_metal(seed=1)),
        ("panel-cream-screws", M.painted_metal(seed=2, base=(200, 194, 172), screws=True, chips=6)),
        ("plain-grey", M.painted_metal(seed=3, base=(110, 112, 112), panel=False, chips=3)),
        ("panel-blue-worn", M.scratches(M.rust(M.painted_metal(seed=4, base=(64, 86, 116), chips=8), 0.08, 4, edges=True), 6, 4)),
    ]),
    "brushed_metal": (["block/metal/plate/stainlesssteel", "block/metal/plate/steel"], lambda: [
        ("steel-h", M.brushed_metal(seed=1)),
        ("alu-v", M.brushed_metal(seed=2, base=(176, 178, 180), direction="v")),
        ("dark-h", M.brushed_metal(seed=3, base=(112, 114, 118), streak=7, sheen=6)),
    ]),
    "galvanised": (["block/metal/plate/zinc", "block/metal/plate/tin"], lambda: [
        ("default", M.galvanised(seed=1)),
        ("coarse", M.galvanised(seed=2, cells=12, spangle=14)),
        ("weathered", M.galvanised(seed=3, base=(134, 138, 136), white_rust=0.6, spangle=8)),
    ]),
    "riveted_plate": (["block/metal/riveted/iron1", "block/metal/riveted/iron3"], lambda: [
        ("edges", M.riveted_plate(seed=1)),
        ("grid", M.riveted_plate(seed=2, layout="grid", seam=False, base=(104, 100, 96))),
        ("rusty-edges", M.riveted_plate(seed=3, base=(96, 90, 84), rust_amount=0.12)),
        ("green-pitch6", M.riveted_plate(seed=4, base=(82, 100, 88), pitch=6)),
    ]),
    "wood_planks": (["block/wood/planks/oak1", "block/wood/planks/aged1"], lambda: [
        ("oak-3", M.wood_planks(seed=1)),
        ("oak-3-alt-knot-joint", M.wood_planks(seed=5, knots=1, joints=0.4)),
        ("mahogany-4", M.wood_planks(seed=2, base=(112, 56, 40), planks=4, contrast=0.8)),
        ("pale-v", M.wood_planks(seed=3, base=(184, 150, 104), direction="v")),
        ("grey-old", M.scratches(M.wood_planks(seed=4, base=(124, 112, 96), per_plank=14, contrast=1.3, joints=0.3), 4, 4, light=0.1)),
    ]),
    "fabric": (["block/cloth/linen/green", "block/cloth/wool/gray1", "block/cloth/burlap/sides"], lambda: [
        ("plain-green", M.fabric(seed=1)),
        ("twill-navy", M.fabric(seed=2, base=(62, 70, 98), weave="twill", contrast=12)),
        ("basket-burlap", M.fabric(seed=3, base=(170, 142, 100), weave="basket", contrast=14, thread=5)),
        ("ripstop-tent", M.fabric(seed=4, base=(92, 112, 72), weave="ripstop", contrast=7)),
    ]),
    "carpet": (["block/cloth/smallcarpet/brown", "block/cloth/mediumcarpet/blue"], lambda: [
        ("level0-tan", M.carpet(seed=1)),
        ("office-grey-loop", M.carpet(seed=2, base=(122, 120, 112), loop=True, tone2=(98, 102, 108), mix2=0.4)),
        ("hotel-red-pattern", M.carpet(seed=3, base=(150, 54, 46), pattern=_rug_motif(), nap="s")),
        ("worn-blue", M.carpet(seed=4, base=(70, 84, 118), wear=1.0, nap="e")),
    ]),
    "tile": (["block/clay/tile/2x2/plain/black1", "block/stone/tiles/travertine1"], lambda: [
        ("white-8", M.tile(seed=1)),
        ("glazed-cream-running", M.tile(seed=2, base=(214, 200, 160), pitch=(16, 8), offset=0.5, crazing=0.4)),
        ("mosaic-pool", M.tile(seed=3, pitch=4, mosaic=[(70, 140, 170), (90, 160, 186), (60, 120, 156), (200, 214, 214)],
                               jitter=4, uneven=2, grout=(176, 180, 176))),
        ("floor-grey-16", M.tile(seed=4, base=(150, 148, 142), pitch=16, glaze=False, grout=(92, 88, 82), uneven=6, speckle=0.6)),
    ]),
    "glass": (["block/glass/plain", "block/glass/vintage"], lambda: [
        ("clear", M.glass(seed=1)),
        ("dusty", M.glass(seed=2, base=(186, 196, 186), dust=0.08, alpha=140)),
        ("no-edge", M.glass(seed=3, edge=False, streaks=3)),
    ]),
    "rubber": (["block/leather/black", "block/leather/gray"], lambda: [
        ("plain", M.rubber(seed=1)),
        ("studs", M.rubber(seed=2, pattern="studs")),
        ("ribs", M.rubber(seed=3, pattern="ribs", base=(56, 52, 50))),
        ("diamond", M.rubber(seed=4, pattern="diamond")),
    ]),
    "asphalt": (["block/stone/gravel/andesite", "block/stone/path/normal1"], lambda: [
        ("road", M.asphalt(seed=1)),
        ("old", M.asphalt(seed=2, base=(84, 82, 80))),
        ("old-alt-cracked", M.asphalt(seed=4, base=(84, 82, 80), cracks=2)),
        ("fresh-dark", M.asphalt(seed=3, base=(48, 48, 50), aggregate=0.2, binder=0.6)),
    ]),
    "brick": (["block/stone/brick/andesite1", "block/clay/brick/four/running/brown1"], lambda: [
        ("red-running", M.brick(seed=1)),
        ("white-block-16x32", M.brick(seed=2, base=(206, 204, 196), mortar=(170, 168, 160), course=16, length=32, chamfer=True,
                                      jitter=5, hue=2, pits=0.01)),
        ("cinder-8x16", M.brick(seed=3, base=(138, 136, 130), mortar=(112, 110, 104), chamfer=True, pits=0.12, jitter=8, hue=2)),
        ("tunnel-dark-stack", M.brick(seed=4, base=(96, 70, 58), mortar=(70, 66, 60), offset=0, jitter=10)),
    ]),
    "ceiling": (["block/stone/plaster/square", "block/glass/plain"], lambda: [
        ("tile", M.ceiling_tile(seed=1)),
        ("tile-2", M.ceiling_tile(seed=2)),
        ("tile-stain", M.ceiling_tile(seed=3, stain_color=(170, 140, 84))),
        ("tile-2x4", M.ceiling_tile(seed=4, size=(32, 64))),
        ("troffer-on", M.troffer_lens(seed=1)),
        ("troffer-dim", M.troffer_lens(seed=2, lit=0.5)),
        ("troffer-off", M.troffer_lens(seed=3, lit=0.0)),
        ("troffer-red", M.troffer_lens(seed=4, lens=(220, 90, 80), glow=(255, 120, 100))),
    ]),
    "ops": (["block/metal/corroded/rusty1", "block/stone/plaster/plain"], _ops),
    "alternates": (["block/stone/polishedrock/andesite"], _alternates),
}
EDGE_STRUCTURE = {"painted_metal", "riveted_plate", "ceiling"}  # seams on the edge by design


def seam_score(img):
    """The mean colour step across the wrap edge over the largest step across any other column (row) boundary, the
    worse of the two axes. A seamless texture scores about 1 or under: its wrap is no stronger than the lines its own
    structure draws inside (plank gaps, grout, strip seams). Over 1.15 means the wrap edge is the strongest line in it."""
    p, (w, h) = img.convert("RGB").load(), img.size

    def step(a, b):
        return sum(abs(a[i] - b[i]) for i in range(3))
    cols = [sum(step(p[b, y], p[(b + 1) % w, y]) for y in range(h)) / h for b in range(w)]
    rows = [sum(step(p[x, b], p[x, (b + 1) % h]) for x in range(w)) / w for b in range(h)]
    return max(cols[-1] / max(1e-6, max(cols[:-1])), rows[-1] / max(1e-6, max(rows[:-1])))


# ---------------- Model helpers (modelkit.py) rendered with sample textures ----------------

def dial_face(size=32, ink=(40, 36, 32), paper=(226, 220, 198)):
    """A sample printed dial: a cream disc with ticks and a red zone, transparent outside the disc."""
    im = M.noise_hv(paper, 3, 9, size, 3)
    p = im.load()
    c = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            d = ((x - c) ** 2 + (y - c) ** 2) ** 0.5
            if d > c + 0.3:
                p[x, y] = (0, 0, 0, 0)
            elif d > c - 1.2:
                p[x, y] = M.rgba(M.lift(paper, -40))
    import math
    for k in range(11):
        a = math.radians(-135 + 27 * k)
        for r in range(int(c * 0.62), int(c * 0.86)):
            x, y = round(c + r * math.sin(a)), round(c - r * math.cos(a))
            p[x, y] = M.rgba((170, 40, 32) if k >= 9 else ink)
    return im


def sample_textures():
    t = {}
    t["tabletop"] = M.wood_planks(seed=21, base=(150, 108, 66), joints=0)
    t["tableedge"] = M.wood_planks(seed=22, base=(126, 88, 54), planks=4, knots=0, joints=0)
    t["tableleg"] = M.wood_planks(seed=23, base=(120, 84, 50), direction="v", planks=4, knots=0, joints=0)
    t["chairseat"] = M.fabric(seed=24, base=(132, 58, 50), weave="twill", contrast=8)
    t["chairseatside"] = M.fabric(seed=25, base=(112, 48, 42), weave="twill", contrast=8)
    t["chairframe"] = M.brushed_metal(seed=26, base=(120, 122, 126), direction="v")
    t["cabinetbody"] = M.painted_metal(seed=27, base=(150, 160, 150), panel=False, chips=2)
    t["cabinetdoor"] = M.painted_metal(seed=28, base=(160, 170, 160), panel=False, chips=3)
    t["cabinettop"] = M.wood_planks(seed=29, base=(170, 140, 100), joints=0, knots=0)
    t["metal"] = M.brushed_metal(seed=30, base=(168, 168, 164))
    t["doorleaf"] = M.wood_planks(seed=31, base=(140, 100, 64), direction="v", planks=1, knots=0, joints=0)
    t["doorleafedge"] = M.wood_planks(seed=32, base=(120, 84, 54), direction="v", planks=2, knots=0, joints=0)
    t["doorpaint"] = M.painted_metal(seed=42, base=(208, 202, 184), panel=False, chips=2)
    t["doorframe"] = M.painted_metal(seed=33, base=(196, 190, 172), panel=False, chips=2)
    t["firedoor"] = M.painted_metal(seed=34, base=(150, 54, 44), panel=False, chips=4)
    t["glass"] = M.glass(seed=35, alpha=150)
    t["dialface"] = dial_face()
    t["needle"] = M.noise_hv((180, 40, 32), 3, 36, mottle=2)
    t["dark"] = M.rubber(seed=37, base=(34, 34, 36))
    t["keypadplate"] = M.brushed_metal(seed=38, base=(110, 112, 116))
    t["key"] = M.painted_metal(seed=39, base=(206, 202, 190), panel=False, chips=0)
    t["wall"] = M.painted_metal(seed=40, base=(96, 112, 104), screws=True, chips=3)
    t["grillebody"] = M.painted_metal(seed=41, base=(176, 174, 166), panel=False, chips=1)
    return t


def model_set():
    import modelkit as K
    sets = {}
    sets["chair-panel"] = K.chair()
    sets["chair-slats"] = K.chair("Chair", back_style="slats", seat={"top": "tabletop", "side": "tableedge"}, frame="tableleg")
    sets["table"] = K.table()
    sets["table-small-foot"] = K.table("T", 3, 3, 13, 13, h=11, top={"top": "cabinettop", "side": "chairframe"},
                                       legs="chairframe", apron=0, lip=0.5, leg_t=1.0, foot=0.5)
    sets["cabinet"] = K.cabinet(drawers=1)
    sets["door-panelled"] = K.door()
    sets["door-painted-4panel"] = K.door(leaf={"front": "doorpaint", "side": "doorpaint"}, panels=(2, 2), raised=0.5)
    sets["door-fire-pushbar-window"] = K.door(leaf={"front": "firedoor", "side": "firedoor"}, push=True, window=True, panels=(1, 2))
    sets["gauge-on-panel"] = [K.box("Wall", (0, 0, 15), (16, 16, 16), "wall")] + K.gauge("G", 8, 9, 15, r=3.0, angle=35) + \
        K.dial("D", 4, 3.5, 15, r=1.75, angle=-60, bezel="metal")
    sets["grille-and-keypad"] = [K.box("Wall", (0, 0, 15), (16, 16, 16), "wall")] + \
        K.grille("V", (2, 7, 13), (11, 14, 15), "grillebody", bars=6) + K.keypad("K", 12, 6, 15, cols=3, rows=4, key=0.75, gap=0.25)
    sets["hardware-board"] = [K.box("Wall", (0, 0, 15), (16, 16, 16), "doorleaf")] + \
        K.handle("H", 3, 10, 15, 5, "y") + K.knob("N", 8, 12, 15) + K.lever("L", 11, 7, 15, 3.0, side=1) + \
        K.hinge("Hi", 14.5, 10, 15, 15, side="right") + K.kick_plate("Kp", 1, 15, 0.5, 4, 15) + \
        K.handle("H2", 8, 6, 15, 4, "x", 0.75, 0.5)
    sets["bevelled-and-panels"] = K.bevelled_box("B", (1, 0, 9), (6, 5, 14), {"top": "cabinettop", "side": "cabinetbody"}, 0.5) + \
        K.inset_panel("I", (8, 0, 10), (15, 8, 15), "cabinetbody", panel="cabinetdoor", grid=(2, 2), border=1.0) + \
        K.frame_and_panel("F", (1, 6, 3), (7, 16, 4.5), {"front": "doorleaf", "side": "doorleafedge"}, border=1.5, grid=(1, 2), raised=0.5)
    sets["turned-west"] = K.turn(K.gauge("G", 8, 9, 15, r=3.0, angle=35) + [K.box("Wall", (0, 0, 15), (16, 16, 16), "wall")], 3)
    return sets


def props(out):
    import json
    import preview_shapes as P
    tdir, sdir = os.path.join(out, "tex", "props"), os.path.join(out, "shapes")
    os.makedirs(tdir, exist_ok=True)
    os.makedirs(sdir, exist_ok=True)
    for f in os.listdir(sdir):
        if f.endswith(".json"):
            os.remove(os.path.join(sdir, f))
    for k, im in sample_textures().items():
        im.save(os.path.join(tdir, k + ".png"))
        P._images["b2/" + k] = im
    files = []
    for name, els in model_set().items():
        import modelkit as K
        data = {"textureWidth": 16, "textureHeight": 16, "textures": {k: "b2/" + k for k in K.textures(els)}, "elements": els}
        path = os.path.join(sdir, name + ".json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1)
        files.append(path)
    cell, cols = 384, 4
    from PIL import ImageDraw
    sheet = Image.new("RGBA", (cols * cell, ((len(files) + cols - 1) // cols) * (cell + 16)), (30, 30, 30, 255))
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(files):
        x, y = (i % cols) * cell, (i // cols) * (cell + 16)
        sheet.alpha_composite(P.render(f, cell), (x, y))
        d.text((x + 4, y + cell + 1), os.path.basename(f)[:-5], fill=(255, 255, 255, 255), font=texsheet.font(13))
    sheet.save(os.path.join(out, "models.png"))
    print(f"{os.path.join(out, 'models.png')}: {len(files)} models; shapes in {sdir}")




# ---------------- Entity shading (rig.shade_fill against rig.fill) ----------------

def entity(out):
    """The same small creature painted with rig.fill and with rig.shade_fill, rendered by entrender (nothing saved
    under assets: the model is built and painted in memory)."""
    import rig
    import entrender as E
    from PIL import ImageDraw
    cols = []
    for label, painter in (("rig.fill", rig.fill), ("rig.shade_fill", rig.shade_fill)):
        m = rig.Model("b2demo", atlas_width=64, seed=3)
        skin, dark = (150, 128, 104), (96, 84, 72)
        body = m.part("Body", (-8, 8, -4), (16, 8, 8), paint=lambda c, b=skin: painter(c, b))
        m.part("Head", (-14, 11, -3), (6, 6, 6), parent=body, paint=lambda c, b=skin: painter(c, b))
        m.part("Snout", (-17, 11, -1.5), (3, 3, 3), parent="Head", paint=lambda c, b=dark: painter(c, b))
        for i, (x, z) in enumerate(((-6, -3.5), (4, -3.5), (-6, 1.5), (4, 1.5))):
            m.part(f"Leg{i}", (x, 0, z), (2, 8, 2), parent=body, paint=lambda c, b=dark: painter(c, b))
        shape, (w, h) = m.shape()
        tex = m._paint(w, h)
        views = []
        for yaw, pitch in ((-40, 20), (0, 0), (-90, 0)):
            views.append(E.render(shape, tex, E.pose_at(None, 0), yaw, pitch, 110, (300, 260), 30))
        big = tex.resize((tex.width * 4, tex.height * 4), Image.NEAREST)
        cols.append((label, views, big))
    W = 300 * 3 + max(c[2].width for c in cols) + 30
    H = 2 * 290
    sheet = Image.new("RGB", (W, H), (30, 30, 34))
    d = ImageDraw.Draw(sheet)
    for r, (label, views, big) in enumerate(cols):
        for i, v in enumerate(views):
            sheet.paste(v, (i * 300, r * 290 + 26))
        sheet.paste(big.convert("RGB"), (900 + 20, r * 290 + 26))
        d.text((6, r * 290 + 4), label, fill=(255, 255, 255), font=texsheet.font(16))
    path = os.path.join(out, "entity-shading.png")
    sheet.save(path)
    print(f"{path}: rig.fill against rig.shade_fill")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("families", nargs="*")
    ap.add_argument("--out", default=os.path.join(ROOT, "review", "b2"))
    a = ap.parse_args()
    if not a.families or "models" in a.families:
        props(a.out)
    if not a.families or "entity" in a.families:
        entity(a.out)
    for fam, (refs, make) in FAMILIES.items():
        if a.families and fam not in a.families:
            continue
        folder = os.path.join(a.out, "tex", fam)
        os.makedirs(folder, exist_ok=True)
        for f in os.listdir(folder):
            if f.endswith(".png"):
                os.remove(os.path.join(folder, f))
        entries = []
        for k, (label, img) in enumerate(make()):
            M.wh(img.size)
            path = os.path.join(folder, f"{k:02d}-{label}.png")
            img.save(path)
            entries.append((path, f"{k:02d}-{label}.png"))
            sc = seam_score(img)
            flag = "" if sc < 1.15 else (" (edge structure by design)" if fam in EDGE_STRUCTURE else "  <-- SEAM?")
            print(f"{fam:14s} {label:24s} {img.width}x{img.height}  seam {sc:4.2f}{flag}")
        opts = SimpleNamespace(max=256, tile=False, per_page=0, scale=4, cols=None)
        texsheet.make(entries, texsheet.ref_entries(refs), os.path.join(a.out, fam + ".png"), opts)
        if fam not in ("ops",):
            opts.tile = True
            texsheet.make([e for e in entries if Image.open(e[0]).width <= 64], texsheet.ref_entries(refs),
                          os.path.join(a.out, fam + "-tile.png"), opts)


if __name__ == "__main__":
    main()
