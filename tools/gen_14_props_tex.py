"""Level 14 "The Hospital": the textures of the level's furniture and equipment (called from tools/gen_14_props.py).

Every texture here is textures/block/14/p-*.png (the p- prefix keeps them apart from the surfaces' own textures in the
same folder), 32 px a block; pictures (a magazine cover, screens, the knives behind glass, stencils) are mapped over a
whole face. Palette (docs/design/experimental-levels/14-plan.md section 4): inpatient "blinding white" (238, 240, 238)
gone a little dull, with sparse corrosion and moss; rust (138, 72, 38); old blood (92, 10, 12); mould and moss (66, 82,
40) and (34, 38, 30); the reception's tired oak veneer and teal vinyl; T.14.R.G.'s olive drab.
"""
import math
import os
import random
import zlib

from PIL import Image, ImageDraw

import matlib as M
from gen_textures import check_atlas_grid
from gen_3999_kit import F3, F5, draw_text, text_width

S = 32
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
TEX = os.path.join(ROOT, "assets", "backrooms", "textures", "block", "14")
WRITTEN = []

WHITE = (238, 240, 238)
RUST = (138, 72, 38)
RUSTDARK = (84, 46, 30)
BLOOD = (92, 10, 12)
MOSS = (66, 82, 40)
MOSSDARK = (34, 38, 30)
MINT = (176, 206, 188)
TEAL = (98, 140, 128)
OLIVE = (88, 94, 58)
STEEL = (176, 180, 184)
CHROME = (206, 210, 216)


def seed_of(name):
    return zlib.crc32(("l14p-" + name).encode()) & 0xFFFF


def save(img, name):
    name = "p-" + name
    check_atlas_grid(img, f"block/14/{name}.png")
    os.makedirs(TEX, exist_ok=True)
    img.save(os.path.join(TEX, name + ".png"))
    WRITTEN.append(name)


def rgba(c, a=255):
    return M.rgba(c, a)


def gloss(c, seed, side=False, amp=1.5, size=S):
    """Enamel or moulded plastic: the colour, a broad soft sheen up and to the left, a fine grain; a side face a step
    darker with no sheen."""
    base = M.lift(c, -12) if side else c
    img = M.noise_hv(base, amp, seed, size, mottle=2, cells=(16, 8), hue=0.8)
    if not side:
        px = img.load()
        w, h = img.size
        for y in range(h):
            for x in range(w):
                t = math.exp(-(((x - 9) / 14.0) ** 2 + ((y - 7) / 10.0) ** 2))
                px[x, y] = rgba(M.lift(px[x, y], 5 * t), 255)
    return img


def fleck(img, seed, n=18, dark=(-7, -3), light=(3, 6)):
    rng = random.Random(seed)
    w, h = img.size
    for _ in range(n):
        x, y = rng.randrange(w), rng.randrange(h)
        M.touch(img, x, y, rng.uniform(*dark) / 100 if rng.random() < 0.6 else rng.uniform(*light) / 100)
    return img


def specks(img, seed, n, colours, size=(1, 2)):
    """Small clusters of the given colours (corrosion pits, moss tufts, blood flecks)."""
    rng = random.Random(seed)
    px = img.load()
    w, h = img.size
    for _ in range(n):
        x, y = rng.randrange(w), rng.randrange(h)
        c = rng.choice(colours)
        for _ in range(rng.randint(*size)):
            px[x % w, y % h] = rgba(M.lift(c, rng.uniform(-8, 8)))
            x += rng.choice((-1, 0, 1))
            y += rng.choice((-1, 0, 1))
    return img


def moss_tufts(img, seed, n=4, bias="bottom"):
    """Moss creeping in from an edge: soft clumps of green with dark roots."""
    rng = random.Random(seed)
    px = img.load()
    w, h = img.size
    for _ in range(n):
        cx = rng.randrange(w)
        cy = h - 1 - rng.randrange(0, 6) if bias == "bottom" else rng.randrange(h)
        r = rng.uniform(1.5, 3.5)
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                d = math.hypot(x - cx, (y - cy) * 1.3)
                if d < r and rng.random() < 0.85:
                    c = M.mix(MOSS, MOSSDARK, rng.random() * 0.5 + (d / r) * 0.3)
                    px[x % w, y % h] = rgba(M.lift(c, rng.uniform(-6, 10)))
    return img


def blood(img, seed, n=6, size=(1, 4), dark=True):
    return specks(img, seed, n, [BLOOD, M.lift(BLOOD, -20), (70, 8, 10)] if dark else [BLOOD], size)


def pic(size, bg):
    img = Image.new("RGBA", size, rgba(bg))
    return img, ImageDraw.Draw(img)


# ======================================================================== Materials

def metals():
    # The inpatient white: an enamel a little dulled; the worn one has sparse corrosion and a little moss
    save(gloss(WHITE, seed_of("white"), amp=1.2), "white")
    img = gloss(M.lift(WHITE, -6), seed_of("whiteworn"), amp=1.5)
    M.grime(img, 0.08, seed=seed_of("whitewornG"), color=(176, 172, 160), cells=(8, 4))
    M.rust(img, 0.06, seed=seed_of("whitewornR"), color=RUST, dark=RUSTDARK, pits=True)
    specks(img, seed_of("whitewornS"), 4, [RUST, RUSTDARK], (1, 3))
    moss_tufts(img, seed_of("whitewornM"), 2)
    save(img, "whiteworn")
    save(M.brushed_metal(seed=seed_of("chrome"), base=CHROME, direction="v", streak=6, sheen=14), "chrome")
    save(M.brushed_metal(seed=seed_of("steel"), base=STEEL, streak=6, sheen=8), "steel")
    save(M.brushed_metal(seed=seed_of("darksteel"), base=(86, 90, 96), streak=5, sheen=6), "darksteel")
    img = M.brushed_metal(seed=seed_of("tray"), base=(190, 194, 198), streak=5, sheen=12)
    M.scratches(img, 5, seed=seed_of("trayS"), light=0.12)
    save(img, "tray")
    # Rust: steel gone orange-brown, and steel spotted with it (the rusty trolley, the torture rooms' cabinets)
    img = M.painted_metal(seed=seed_of("rust"), base=(110, 104, 98), panel=False, chips=0)
    M.rust(img, 0.75, seed=seed_of("rustR"), color=RUST, dark=RUSTDARK, cells=(8, 4, 2))
    M.drips(img, 3, seed=seed_of("rustD"), color=(70, 38, 22), strength=0.35)
    save(img, "rust")
    img = M.brushed_metal(seed=seed_of("ruststeel"), base=(150, 150, 148), streak=5, sheen=6)
    M.rust(img, 0.4, seed=seed_of("ruststeelR"), color=RUST, dark=RUSTDARK)
    M.grime(img, 0.2, seed=seed_of("ruststeelG"), color=(60, 50, 40))
    save(img, "ruststeel")
    img = M.painted_metal(seed=seed_of("rustcab"), base=(122, 128, 124), panel=False, chips=4, under=(90, 70, 56))
    M.rust(img, 0.45, seed=seed_of("rustcabR"), color=RUST, dark=RUSTDARK, edges=True)
    M.drips(img, 4, seed=seed_of("rustcabD"), color=(96, 50, 28), strength=0.4, start=2)
    blood(img, seed_of("rustcabB"), 3)
    save(img, "rustcab")
    img = M.painted_metal(seed=seed_of("rustwhite"), base=(214, 214, 206), panel=False, chips=3, under=(110, 80, 60))
    M.rust(img, 0.32, seed=seed_of("rustwhiteR"), color=RUST, dark=RUSTDARK)
    M.grime(img, 0.18, seed=seed_of("rustwhiteG"), color=(96, 80, 60))
    save(img, "rustwhite")
    save(M.noise_hv((34, 34, 38), 2, seed_of("black"), S, mottle=2, hue=0.5), "black")
    save(M.rubber(seed=seed_of("rubber"), base=(40, 40, 42)), "rubber")
    save(gloss((214, 208, 190), seed_of("beige")), "beige")
    save(gloss((214, 208, 190), seed_of("beigeside"), side=True), "beige-side")
    save(gloss((150, 154, 156), seed_of("greyplastic")), "greyplastic")
    save(gloss((62, 64, 70), seed_of("darkplastic")), "darkplastic")
    img = M.noise_hv((176, 140, 66), 3, seed_of("brass"), S, mottle=5, hue=1.0)
    M.grime(img, 0.2, seed=seed_of("brassG"), color=(90, 70, 40))
    save(img, "brass")
    # Olive drab painted steel (the research group's field kit), chipped
    img = M.painted_metal(seed=seed_of("olive"), base=OLIVE, panel=False, chips=4, under=(120, 118, 110))
    M.grime(img, 0.12, seed=seed_of("oliveG"), color=(50, 46, 34))
    save(img, "olive")
    # the anaesthesia machine's grey-green enamel
    img = gloss((168, 184, 176), seed_of("anaes"))
    M.grime(img, 0.12, seed=seed_of("anaesG"), color=(120, 116, 100))
    specks(img, seed_of("anaesS"), 3, [RUST, RUSTDARK], (1, 3))
    save(img, "anaes")
    # Chain: dark rusty links on transparency (a vertical run, links alternately face-on and edge-on)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    rng = random.Random(seed_of("chain"))
    for y in range(S):
        for x in range(S):
            k = y % 8
            if k in (0, 7):
                on = 10 <= x <= 21
            else:
                on = x in (10, 11, 20, 21)
            if on:
                c = M.mix((96, 60, 40), (60, 40, 30), rng.random() * 0.6)
                if x in (10, 20) or k == 0:
                    c = M.lift(c, 22)
                px[x, y] = rgba(M.lift(c, rng.uniform(-6, 6)))
    save(img, "chain")
    img = M.noise_hv((110, 70, 44), 4, seed_of("hook"), S, mottle=8)
    M.rust(img, 0.5, seed=seed_of("hookR"), color=RUST, dark=RUSTDARK)
    blood(img, seed_of("hookB"), 6, (1, 4))
    save(img, "hook")


def fabrics():
    sheet = M.fabric(seed=seed_of("sheet"), base=(234, 236, 232), weave="plain", contrast=4, grain=2, mottle=3)
    save(sheet, "sheet")
    img = M.fabric(seed=seed_of("sheetstain"), base=(226, 226, 216), weave="plain", contrast=4, grain=2, mottle=4)
    M.stain(img, seed=seed_of("sheetstainS"), radius=8, color=(186, 170, 120), strength=0.35, at=(20, 12))
    M.stain(img, seed=seed_of("sheetstainB"), radius=4, color=(120, 30, 26), strength=0.45, at=(8, 24))
    M.grime(img, 0.1, seed=seed_of("sheetstainG"), color=(160, 150, 130))
    save(img, "sheetstain")
    save(M.fabric(seed=seed_of("pillow"), base=(240, 240, 236), weave="plain", contrast=3, grain=2, mottle=4), "pillow")
    # the cellular blanket: pale blue, an open waffle of holes
    img = M.fabric(seed=seed_of("blanket"), base=(168, 196, 214), weave="plain", contrast=5, grain=2, mottle=4)
    for y in range(1, S, 4):
        for x in range(1 + (y // 4) % 2 * 2, S, 4):
            M.touch(img, x, y, -0.16)
            M.touch(img, x + 1, y, -0.1)
    save(img, "blanket")
    img = M.fabric(seed=seed_of("blanketside"), base=(150, 178, 198), weave="plain", contrast=4, grain=2, mottle=3)
    save(img, "blanket-side")
    # the bare mattress: blue wipe-clean vinyl, a seam, stains
    img = M.noise_hv((110, 140, 162), 2, seed_of("mattress"), S, mottle=5, hue=1.0)
    M.emboss_lines(img, ys=(15,), strength=0.12)
    M.stain(img, seed=seed_of("mattressS"), radius=9, color=(150, 136, 90), strength=0.3, at=(10, 10))
    M.stain(img, seed=seed_of("mattressB"), radius=4, color=(70, 14, 14), strength=0.45, at=(24, 22))
    specks(img, seed_of("mattressM"), 3, [MOSSDARK, MOSS], (2, 4))
    save(img, "mattress")
    save(M.noise_hv((92, 118, 138), 2, seed_of("mattressside"), S, mottle=3), "mattress-side")
    # restraint straps: worn brown leather with stitched edges
    img = M.noise_hv((104, 66, 40), 3, seed_of("leather"), S, mottle=6, hue=1.5)
    for x in range(0, S, 2):
        for y in (1, S - 2):
            M.touch(img, x, y, 0.12)
    fleck(img, seed_of("leatherF"), 30)
    save(img, "leather")
    # the privacy curtain: pale green, vertical folds lit and shaded; the top band is open mesh
    img = M.fabric(seed=seed_of("curtain"), base=(168, 204, 184), weave="plain", contrast=4, grain=2, mottle=3)
    px = img.load()
    for y in range(S):
        for x in range(S):
            f = math.sin(x / S * 2 * math.pi * 2)
            px[x, y] = rgba(M.lift(px[x, y], 9 * f))
    M.grime(img, 0.08, seed=seed_of("curtainG"), color=(130, 140, 110), bias="bottom")
    save(img, "curtain")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    for y in range(S):
        for x in range(S):
            if x % 3 == 0 or y % 3 == 0:
                px[x, y] = rgba(M.lift((200, 214, 204), (x * 7 + y * 3) % 9 - 4))
    save(img, "curtainmesh")
    img = M.fabric(seed=seed_of("curtainhem"), base=(156, 192, 172), weave="plain", contrast=4, grain=2, mottle=3)
    M.grime(img, 0.22, seed=seed_of("curtainhemG"), color=(110, 104, 80), bias="bottom")
    blood(img, seed_of("curtainhemB"), 2)
    save(img, "curtainhem")
    # waiting room vinyl: teal, a seam welt; torn: split open on yellowed foam
    img = M.noise_hv((62, 112, 106), 2.5, seed_of("vinyl"), S, mottle=5, hue=1.0)
    M.emboss_lines(img, ys=(2, 29), strength=0.12)
    M.grime(img, 0.1, seed=seed_of("vinylG"), color=(50, 60, 54))
    fleck(img, seed_of("vinylF"), 14)
    save(img, "vinyl")
    save(M.noise_hv((48, 90, 86), 2, seed_of("vinylside"), S, mottle=3), "vinyl-side")
    img = Image.open(os.path.join(TEX, "p-vinyl.png")).convert("RGBA")
    px = img.load()
    rng = random.Random(seed_of("vinyltorn"))
    for (cx, cy, r) in ((13, 15, 7), (24, 8, 3)):
        pts = [(cx + math.cos(t) * r * rng.uniform(0.6, 1.1), cy + math.sin(t) * r * 0.55 * rng.uniform(0.6, 1.1)) for t in [i / 9 * 2 * math.pi for i in range(9)]]
        mask = Image.new("L", (S, S), 0)
        ImageDraw.Draw(mask).polygon(pts, fill=255)
        mp = mask.load()
        for y in range(S):
            for x in range(S):
                if mp[x, y]:
                    px[x, y] = rgba(M.lift((214, 186, 116), rng.uniform(-14, 8)))
                elif any(mp[min(S - 1, max(0, x + dx)), min(S - 1, max(0, y + dy))] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    px[x, y] = rgba(M.lift(px[x, y], 26))
    save(img, "vinyltorn")
    save(M.noise_hv((210, 182, 112), 4, seed_of("foam"), S, mottle=8), "foam")
    # a lamp shade: cream linen, foxed; lit: glowing warm from inside
    img = M.fabric(seed=seed_of("shade"), base=(214, 198, 160), weave="plain", contrast=5, grain=2, mottle=5)
    M.stain(img, seed=seed_of("shadeS"), radius=5, color=(160, 130, 80), strength=0.3, at=(22, 20))
    save(img, "shade")
    img = M.fabric(seed=seed_of("shadelit"), base=(255, 226, 164), weave="plain", contrast=5, grain=2, mottle=5)
    px = img.load()
    for y in range(S):
        for x in range(S):
            px[x, y] = rgba(M.lift(px[x, y], 10 * (1 - abs(y - 16) / 16)))
    M.stain(img, seed=seed_of("shadelitS"), radius=5, color=(200, 150, 90), strength=0.3, at=(22, 20))
    save(img, "shadelit")
    save(M.new((S, S), (255, 236, 190)), "bulb")
    # stretcher canvas: khaki, filthy, old blood soaked in
    img = M.fabric(seed=seed_of("canvas"), base=(128, 118, 88), weave="basket", contrast=8, grain=3, mottle=6)
    M.stain(img, seed=seed_of("canvasB"), radius=8, color=(70, 14, 12), strength=0.55, at=(12, 16))
    M.grime(img, 0.25, seed=seed_of("canvasG"), color=(60, 50, 36))
    save(img, "canvas")
    # surgical drape: green; stained for the rusty trolley
    save(M.fabric(seed=seed_of("drape"), base=(70, 126, 110), weave="plain", contrast=5, grain=2, mottle=4), "drape")
    img = M.fabric(seed=seed_of("drapestain"), base=(66, 110, 96), weave="plain", contrast=5, grain=2, mottle=5)
    M.stain(img, seed=seed_of("drapestainB"), radius=7, color=(60, 18, 14), strength=0.6, at=(18, 12))
    M.grime(img, 0.2, seed=seed_of("drapestainG"), color=(60, 56, 40))
    save(img, "drapestain")
    save(M.fabric(seed=seed_of("gauze"), base=(240, 238, 230), weave="basket", contrast=8, grain=2, mottle=3), "gauze")
    # the teddy: a worn brown plush, rubbed bald in places, a pale muzzle and paws, a stitched patch
    img = M.noise_hv((132, 92, 58), 6, seed_of("teddy"), S, mottle=8, hue=1.5)
    rng = random.Random(seed_of("teddyF"))
    px = img.load()
    for _ in range(140):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = rgba(M.lift(px[x, y], rng.choice((-18, 14))))
    M.grime(img, 0.2, seed=seed_of("teddyG"), color=(90, 70, 50))
    save(img, "teddy")
    img = M.noise_hv((206, 180, 140), 4, seed_of("teddymuzzle"), S, mottle=6)
    M.grime(img, 0.15, seed=seed_of("teddymuzzleG"), color=(140, 120, 90))
    save(img, "teddymuzzle")
    img = M.fabric(seed=seed_of("teddypatch"), base=(150, 60, 64), weave="plain", contrast=8)
    for k in range(0, S, 3):
        for (x, y) in ((k, 0), (k, S - 1), (0, k), (S - 1, k)):
            img.load()[x % S, y % S] = rgba((230, 220, 200))
    save(img, "teddypatch")
    save(M.fabric(seed=seed_of("babyblanket"), base=(232, 190, 200), weave="plain", contrast=6, grain=2, mottle=4), "babyblanket")
    save(M.fabric(seed=seed_of("babyblanketb"), base=(178, 206, 230), weave="plain", contrast=6, grain=2, mottle=4), "babyblanketblue")
    # the laundry bag: a blue polyester sack
    img = M.fabric(seed=seed_of("linenbag"), base=(70, 104, 160), weave="ripstop", contrast=6, grain=2, mottle=5)
    M.grime(img, 0.12, seed=seed_of("linenbagG"), color=(50, 60, 70), bias="bottom")
    save(img, "linenbag")
    # folded linen seen edge on: a stack of folds
    img = M.fabric(seed=seed_of("linenstack"), base=(232, 234, 228), weave="plain", contrast=3, grain=2, mottle=2)
    for y in range(0, S, 4):
        for x in range(S):
            M.touch(img, x, y, -0.16)
            M.touch(img, x, (y + 1) % S, 0.06)
    save(img, "linenstack")


def woods_and_surfaces():
    # the reception desk's front: a tired light-oak veneer, vertical grain, a little scuffed at the foot
    img = M.wood_planks(seed=seed_of("veneer"), base=(170, 132, 88), planks=2, direction="v", grain=3, contrast=0.6, per_plank=4)
    M.grime(img, 0.1, seed=seed_of("veneerG"), color=(90, 70, 50), bias="bottom")
    save(img, "veneer")
    save(M.wood_planks(seed=seed_of("veneerh"), base=(158, 122, 80), planks=1, direction="h", grain=3, contrast=0.6, per_plank=4), "veneer-side")
    img = M.noise_hv((216, 210, 196), 1.5, seed_of("worktop"), S, mottle=3, hue=0.8)
    fleck(img, seed_of("worktopF"), 30)
    M.stain(img, seed=seed_of("worktopS"), radius=5, color=(170, 150, 110), strength=0.18, at=(22, 10))
    save(img, "worktop")
    img = M.noise_hv(TEAL, 2, seed_of("teal"), S, mottle=3, hue=1.0)
    fleck(img, seed_of("tealF"), 16)
    save(img, "teal")
    img = M.noise_hv((226, 228, 222), 1.5, seed_of("laminate"), S, mottle=3)
    M.bevel(img, (0, 0, S - 1, S - 1), 1, 0.08)
    M.grime(img, 0.12, seed=seed_of("laminateG"), color=(170, 168, 150), bias="bottom")
    save(img, "laminate")
    img = M.noise_hv(MINT, 2, seed_of("mintlam"), S, mottle=3)
    M.grime(img, 0.1, seed=seed_of("mintlamG"), color=(120, 130, 110), bias="bottom")
    save(img, "mintlam")
    img = M.wood_planks(seed=seed_of("crate"), base=(150, 118, 76), planks=3, grain=4, knots=1, joints=0.0)
    M.grime(img, 0.15, seed=seed_of("crateG"), color=(80, 66, 46))
    save(img, "crate")
    img = Image.open(os.path.join(TEX, "p-crate.png")).convert("RGBA")
    # the T.14.R.G. stencil, sprayed black and a little patchy, with a hazard band under it
    st = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw_text(st, "T.14.R.G.", 1, 8, (20, 20, 18, 255), F3)
    draw_text(st, "SUPPLY", 5, 15, (20, 20, 18, 255), F3)
    rng = random.Random(seed_of("stencil"))
    sp, ip = st.load(), img.load()
    for y in range(S):
        for x in range(S):
            if sp[x, y][3] and rng.random() < 0.88:
                ip[x, y] = rgba(M.mix(ip[x, y], (24, 22, 20), 0.85))
    for x in range(3, 29):
        if (x // 3) % 2 == 0:
            ip[x, 23] = ip[x, 24] = rgba((40, 36, 30))
    save(img, "cratestencil")
    save(M.wood_planks(seed=seed_of("bench"), base=(176, 140, 96), planks=2, grain=3, contrast=0.8), "benchwood")
    save(M.wood_planks(seed=seed_of("tuberack"), base=(150, 112, 70), planks=1, grain=3, contrast=0.8), "rackwood")


def glass_and_liquids():
    save(M.glass(seed=seed_of("glass"), base=(206, 222, 220), alpha=60, streaks=2), "glass")
    img = M.glass(seed=seed_of("glasscrack"), base=(206, 222, 220), alpha=70, streaks=1)
    d = ImageDraw.Draw(img)
    for (a, b) in (((16, 14), (2, 4)), ((16, 14), (30, 6)), ((16, 14), (6, 30)), ((16, 14), (28, 28)), ((16, 14), (18, 0))):
        d.line([a, b], fill=(240, 246, 244, 200))
    save(img, "glasscrack")
    # the containment panels: thick glass, green in its depth, bolted
    save(M.glass(seed=seed_of("cellglass"), base=(170, 210, 196), alpha=108, streaks=2, edge=True), "cellglass")
    save(M.glass(seed=seed_of("tubeglass"), base=(222, 236, 236), alpha=140, streaks=1, edge=True), "tubeglass")
    save(M.glass(seed=seed_of("acrylic"), base=(224, 234, 236), alpha=96, streaks=1, edge=True), "acrylic")
    img = M.noise_hv((150, 196, 184), 2, seed_of("shard"), S, mottle=3)
    M.scratches(img, 4, seed=seed_of("shardS"), light=0.2)
    save(img, "shard")
    # soft-drink bottles: green and brown glass, the green one half full of something stale; a red label
    for name, c, fill in (("bottlegreen", (58, 120, 70), None), ("bottlestale", (58, 120, 70), (60, 48, 22)),
                          ("bottlebrown", (110, 62, 26), None)):
        img = M.noise_hv(c, 2, seed_of(name), S, mottle=3, hue=0.5)
        px = img.load()
        for y in range(S):
            for x in range(S):
                cc = px[x, y]
                if fill and y > 15:
                    cc = M.mix(cc, fill, 0.7)
                if x in (6, 7):
                    cc = M.lift(cc, 40)
                px[x, y] = rgba(cc)
        M.grime(img, 0.18, seed=seed_of(name + "G"), color=(90, 86, 70))
        save(img, name)
    img, d = pic((S, S), (186, 30, 34))
    d.line([(0, 18), (8, 12), (16, 18), (24, 12), (31, 18)], fill=(240, 236, 226, 255), width=2)
    draw_text(img, "COLA", 8, 4, (250, 246, 236, 255), F3)
    M.grime(img, 0.2, seed=seed_of("labelG"), color=(110, 80, 60))
    save(img, "sodalabel")
    img, d = pic((S, S), (220, 224, 40))
    d.ellipse([10, 8, 22, 20], fill=(255, 140, 20, 255))
    draw_text(img, "FIZZ", 8, 22, (40, 40, 160, 255), F3)
    M.grime(img, 0.2, seed=seed_of("label2G"), color=(110, 90, 60))
    save(img, "sodalabel2")
    save(M.noise_hv((200, 40, 34), 2, seed_of("cap"), S, mottle=2), "cap")
    # liquids in test tubes and vials
    for name, c in (("liqred", (176, 30, 34)), ("liqgreen", (90, 190, 70)), ("liqamber", (210, 150, 40)),
                    ("liqblue", (60, 120, 200)), ("liqpurple", (130, 60, 160))):
        img = M.noise_hv(c, 3, seed_of(name), S, mottle=5)
        px = img.load()
        for y in range(S):
            for x in range(S):
                if x % 8 in (1, 2):
                    px[x, y] = rgba(M.lift(px[x, y], 30))
        save(img, name)
    img = M.noise_hv((210, 222, 222), 2, seed_of("tube"), S, mottle=2)
    M.grime(img, 0.12, seed=seed_of("tubeG"), color=(140, 150, 120))
    save(img, "tube")
    # Compound 14: black glass, a dull sickly green glow deep inside
    img = M.noise_hv((16, 20, 16), 2, seed_of("vial"), S, mottle=3)
    px = img.load()
    for y in range(S):
        for x in range(S):
            t = 0.5 + 0.5 * math.sin(y / 5.0 + x * 0.3)
            px[x, y] = rgba(M.mix(px[x, y], (60, 110, 30), 0.25 * t))
            if x % 8 == 2:
                px[x, y] = rgba(M.lift(px[x, y], 26))
    save(img, "vial")
    img = M.noise_hv((116, 170, 40), 5, seed_of("vialglow"), S, mottle=8)
    save(img, "vialglow")
    # green ooze from a leaking drum: a glowing pool with ragged edges (cut out), and a run down the drum
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    rng = random.Random(seed_of("ooze"))
    blobs = [(15, 16, 11), (8, 22, 6), (23, 10, 6), (24, 24, 4)]
    for y in range(S):
        for x in range(S):
            inside = max(1 - math.hypot(x - bx, y - by) / r for bx, by, r in blobs)
            inside += (rng.random() - 0.5) * 0.18
            if inside > 0:
                c = M.mix((120, 230, 60), (40, 120, 20), min(1, max(0, 1 - inside * 2.2)))
                if rng.random() < 0.05:
                    c = M.lift(c, 40)
                px[x, y] = rgba(c)
    save(img, "ooze")
    save(M.noise_hv((110, 214, 56), 6, seed_of("oozeside"), S, mottle=8), "oozeflat")


def organic():
    # moss: a soft green cushion; mould: black-green bloom
    img = M.noise_hv(MOSS, 6, seed_of("moss"), S, mottle=10, hue=2.0)
    specks(img, seed_of("mossS"), 40, [M.lift(MOSS, 26), MOSSDARK, (90, 110, 50)], (1, 2))
    save(img, "moss")
    img = M.noise_hv(MOSSDARK, 5, seed_of("mould"), S, mottle=8)
    specks(img, seed_of("mouldS"), 30, [(20, 22, 18), (60, 74, 40), (90, 100, 70)], (1, 3))
    save(img, "mould")
    # the mould carpet: patches of black-green and grey fuzz with ragged holes where the floor shows through
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    f = M.fbm((S, S), seed_of("mouldfloor"), cells=(16, 8, 4))
    rng = random.Random(seed_of("mouldfloorR"))
    for y in range(S):
        for x in range(S):
            v = f[y][x] if isinstance(f, list) else f[y, x]
            if v > -0.3:
                t = min(1, (v + 0.3) * 1.6)
                c = M.mix((58, 72, 40), (20, 24, 18), t)
                if rng.random() < 0.08:
                    c = (130, 136, 110)
                px[x, y] = rgba(M.lift(c, rng.uniform(-6, 6)))
    save(img, "mouldfloor")
    # leaves for the vines (cut out): small dark-green leaves on a trailing stem
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rng = random.Random(seed_of("vines"))
    d.line([(2, 31), (8, 22), (14, 18), (20, 10), (27, 2)], fill=(70, 70, 40, 255), width=1)
    d.line([(14, 18), (6, 10), (4, 3)], fill=(70, 70, 40, 255), width=1)
    for _ in range(26):
        x, y = rng.randrange(1, 30), rng.randrange(1, 30)
        c = M.mix((52, 96, 40), (100, 130, 50), rng.random())
        r = rng.choice((1, 2, 2))
        d.ellipse([x - r, y - r // 2 - 1, x + r, y + r // 2 + 1], fill=rgba(c))
        d.point([x - 1, y - 1], fill=rgba(M.lift(c, 30)))
    save(img, "vines")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    f = M.fbm((S, S), seed_of("vinemat"), cells=(8, 4))
    rng = random.Random(seed_of("vinematR"))
    for y in range(S):
        for x in range(S):
            v = f[y][x] if isinstance(f, list) else f[y, x]
            if v > 0.12:
                c = M.mix((44, 84, 36), (96, 128, 52), rng.random())
                if (x + y * 3) % 7 == 0:
                    c = M.lift(c, 26)
                px[x, y] = rgba(c)
    save(img, "vinemat")
    # a sprout growing out of a test tube (cut out)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.line([(16, 31), (16, 12)], fill=(90, 120, 50, 255), width=2)
    for (x, y, s) in ((10, 14, 1), (22, 10, -1), (12, 6, 1), (20, 18, -1)):
        d.ellipse([x - 4, y - 2, x + 4, y + 2], fill=(84, 150, 60, 255))
        d.line([(x - 3 * s, y), (16, y + 3)], fill=(70, 120, 40, 255))
    save(img, "sprout")
    # blood: a pool (cut out, glossy) and dried smears
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    rng = random.Random(seed_of("bloodpool"))
    blobs = [(15, 15, 10), (6, 24, 5), (24, 8, 5), (25, 22, 3), (5, 8, 2.5)]
    for y in range(S):
        for x in range(S):
            inside = max(1 - math.hypot(x - bx, y - by) / r for bx, by, r in blobs)
            inside += (rng.random() - 0.5) * 0.14
            if inside > 0:
                c = M.mix((72, 6, 8), (118, 14, 16), min(1, inside * 1.6))
                if 0.08 < inside < 0.16:
                    c = (56, 6, 8)
                px[x, y] = rgba(c)
    for (x, y) in ((12, 11), (13, 11), (12, 12), (19, 17)):
        px[x, y] = rgba((190, 80, 80))
    save(img, "bloodpool")
    img = M.noise_hv(BLOOD, 4, seed_of("blood"), S, mottle=8)
    save(img, "blood")


# ======================================================================== Pictures

def pictures():
    # A crumpled magazine: a masthead, a face with no features, "WHERE DO THE HALLS GO?"
    img, d = pic((S, S), (226, 220, 204))
    d.rectangle([0, 0, 31, 7], fill=(170, 30, 40, 255))
    draw_text(img, "LIFE", 2, 1, (250, 246, 236, 255), F5)
    d.ellipse([9, 10, 23, 26], fill=(214, 176, 140, 255))
    d.rectangle([11, 26, 21, 31], fill=(60, 70, 100, 255))
    draw_text(img, "?", 26, 12, (40, 40, 40, 255), F5)
    for y in (27, 29):
        d.line([2, y, 7, y], fill=(60, 60, 60, 255))
    M.grime(img, 0.18, seed=seed_of("magG"), color=(150, 130, 100))
    M.emboss_lines(img, xs=(13,), ys=(18,), strength=0.2)
    save(img, "magazine")
    # a brochure: "LEVEL 14 WELCOMES YOU", a smiling nurse, and a diagram of stairs going down forever
    img, d = pic((S, S), (210, 228, 222))
    d.rectangle([0, 0, 31, 6], fill=(60, 130, 120, 255))
    draw_text(img, "WELCOME", 2, 1, (250, 250, 246, 255), F3)
    d.ellipse([3, 9, 13, 19], fill=(230, 196, 160, 255))
    d.arc([5, 12, 11, 17], 20, 160, fill=(120, 40, 40, 255))
    d.point([(6, 12), (10, 12)], fill=(20, 20, 20, 255))
    for k in range(6):
        d.line([16 + k * 2, 10 + k * 3, 18 + k * 2, 10 + k * 3], fill=(40, 40, 40, 255))
        d.line([18 + k * 2, 10 + k * 3, 18 + k * 2, 13 + k * 3], fill=(40, 40, 40, 255))
    for y in (22, 25, 28):
        d.line([3, y, 14, y], fill=(90, 100, 100, 255))
    M.emboss_lines(img, xs=(10, 21), strength=0.18)
    M.grime(img, 0.12, seed=seed_of("broG"), color=(150, 140, 110))
    save(img, "brochure")
    # printed pages and file papers
    img, d = pic((S, S), (232, 228, 214))
    rng = random.Random(seed_of("papers"))
    for y in range(3, 30, 3):
        d.line([3, y, 3 + rng.randrange(14, 26), y], fill=(110, 110, 110, 255))
    M.grime(img, 0.12, seed=seed_of("papersG"), color=(170, 150, 110))
    save(img, "papers")
    img, d = pic((S, S), (232, 228, 214))
    draw_text(img, "T.14.R.G.", 1, 2, (30, 40, 80, 255), F3)
    d.line([1, 8, 30, 8], fill=(30, 40, 80, 255))
    for y in range(11, 30, 3):
        d.line([2, y, 2 + rng.randrange(12, 28), y], fill=(100, 100, 100, 255))
    d.rectangle([19, 22, 29, 29], outline=(150, 30, 30, 255))
    draw_text(img, "14", 21, 23, (150, 30, 30, 255), F3)
    M.stain(img, seed=seed_of("trgS"), radius=6, color=(120, 90, 50), strength=0.3, at=(8, 22))
    save(img, "trgpaper")
    save(M.noise_hv((200, 170, 90), 2, seed_of("folder"), S, mottle=4), "folder")
    # the vital-signs monitor: on (an ECG trace, SpO2 and pulse numbers in green and cyan), off (a dead dark glass)
    img, d = pic((S, S), (8, 14, 10))
    pts = []
    for x in range(0, 32):
        k = x % 11
        y = 9 - {3: 1, 4: 6, 5: -4, 6: 1}.get(k, 0)
        pts.append((x, y))
    d.line(pts, fill=(90, 250, 110, 255))
    pts2 = [(x, 18 + round(math.sin(x / 2.2) * 1.5)) for x in range(0, 20)]
    d.line(pts2, fill=(80, 200, 240, 255))
    draw_text(img, "72", 22, 14, (90, 250, 110, 255), F3)
    draw_text(img, "98", 22, 22, (80, 200, 240, 255), F3)
    draw_text(img, "120/80", 1, 24, (240, 240, 120, 255), F3)
    save(img, "monitoron")
    img, d = pic((S, S), (22, 26, 26))
    for k in range(10):
        d.point([(5 + k, 4 + k // 2)], fill=(52, 58, 60, 255))
    save(img, "monitoroff")
    # the ventilator's face: a small dead screen, knobs, a pressure scale
    img = gloss((222, 222, 214), seed_of("ventface"))
    d = ImageDraw.Draw(img)
    d.rectangle([3, 3, 28, 13], fill=(18, 24, 22, 255))
    d.line([5, 9, 9, 9, 10, 5, 12, 11, 14, 9, 26, 9], fill=(50, 120, 70, 255))
    for i, x in enumerate((6, 13, 20, 26)):
        d.ellipse([x - 2, 18, x + 2, 22], fill=(60, 64, 70, 255))
        d.point([(x, 18)], fill=(220, 220, 220, 255))
    d.rectangle([3, 26, 28, 28], fill=(70, 150, 200, 255))
    M.grime(img, 0.1, seed=seed_of("ventfaceG"), color=(140, 140, 120))
    save(img, "ventface")
    # the anaesthesia machine's flowmeter bank: glass tubes with bobbins, green, blue, white knobs
    img = gloss((200, 210, 204), seed_of("flow"))
    d = ImageDraw.Draw(img)
    for i, (x, col) in enumerate(((5, (60, 170, 80)), (13, (60, 100, 200)), (21, (230, 230, 230)))):
        d.rectangle([x, 2, x + 5, 24], fill=(214, 230, 232, 255), outline=(120, 130, 130, 255))
        for y in range(4, 24, 3):
            d.point([(x + 1, y)], fill=(80, 90, 90, 255))
        by = 10 + i * 4
        d.rectangle([x + 2, by, x + 3, by + 1], fill=(30, 30, 30, 255))
        d.ellipse([x, 26, x + 5, 31], fill=col + (255,))
    M.grime(img, 0.12, seed=seed_of("flowG"), color=(140, 130, 110))
    save(img, "flowmeter")
    # gauge face
    img, d = pic((S, S), (236, 234, 224))
    d.ellipse([1, 1, 30, 30], outline=(40, 40, 40, 255))
    for k in range(9):
        a = math.radians(-220 + k * 32.5)
        d.line([16 + 11 * math.cos(a), 16 + 11 * math.sin(a), 16 + 14 * math.cos(a), 16 + 14 * math.sin(a)], fill=(30, 30, 30, 255))
    d.arc([3, 3, 28, 28], 20, 60, fill=(200, 40, 40, 255), width=2)
    save(img, "gaugeface")
    save(M.new((S, S), (210, 40, 30)), "needle")
    # gas cylinders: oxygen (white shoulder, black body), nitrous oxide (blue)
    img = M.painted_metal(seed=seed_of("cylblack"), base=(40, 42, 44), panel=False, chips=3, under=(120, 120, 116))
    save(img, "cylblack")
    img = M.painted_metal(seed=seed_of("cylblue"), base=(46, 82, 150), panel=False, chips=3, under=(140, 140, 136))
    save(img, "cylblue")
    save(M.painted_metal(seed=seed_of("cylwhite"), base=(232, 232, 226), panel=False, chips=2, under=(120, 120, 116)), "cylwhite")
    # breathing bag and corrugated hose
    img = M.rubber(seed=seed_of("hose"), base=(70, 110, 150), pattern="ribs", pitch=3)
    save(img, "hose")
    save(M.rubber(seed=seed_of("bag"), base=(36, 36, 38), pattern=None), "breathbag")
    # the beige office computer: a CRT's dim green text; a keyboard
    img, d = pic((S, S), (14, 26, 18))
    rng = random.Random(seed_of("crt"))
    draw_text(img, "LOGIN", 2, 2, (90, 220, 110, 255), F3)
    for y in range(9, 28, 4):
        d.line([2, y, 2 + rng.randrange(6, 26), y], fill=(60, 160, 80, 255))
    d.rectangle([2, 27, 4, 29], fill=(120, 250, 140, 255))
    for y in range(0, S, 2):
        for x in range(S):
            M.touch(img, x, y, -0.12)
    save(img, "crt")
    img = gloss((200, 194, 176), seed_of("keyboard"))
    d = ImageDraw.Draw(img)
    for y in range(3, 29, 6):
        for x in range(2, 30, 4):
            d.rectangle([x, y, x + 2, y + 3], fill=(176, 170, 152, 255))
            d.point([(x, y)], fill=(224, 220, 206, 255))
    save(img, "keyboard")
    # a telephone keypad
    img = gloss((210, 204, 186), seed_of("phonepad"))
    d = ImageDraw.Draw(img)
    for r in range(4):
        for c in range(3):
            d.rectangle([6 + c * 7, 4 + r * 7, 10 + c * 7, 8 + r * 7], fill=(236, 232, 220, 255), outline=(150, 144, 130, 255))
    save(img, "phonepad")
    # the field radio's face: a dial, a speaker grille, knobs
    img = M.painted_metal(seed=seed_of("radioface"), base=(78, 86, 56), panel=False, chips=2, under=(120, 118, 110))
    d = ImageDraw.Draw(img)
    d.rectangle([3, 3, 18, 11], fill=(214, 200, 150, 255), outline=(30, 30, 24, 255))
    for x in range(5, 18, 2):
        d.line([x, 8, x, 10], fill=(40, 40, 30, 255))
    d.line([11, 4, 11, 10], fill=(200, 40, 30, 255))
    for y in range(15, 29, 2):
        d.line([3, y, 17, y], fill=(30, 32, 22, 255))
    for (x, y) in ((24, 6), (24, 16), (24, 25)):
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(26, 26, 24, 255))
        d.point([(x, y - 2)], fill=(200, 200, 190, 255))
    save(img, "radioface")
    # the Compound 14 placard
    img, d = pic((48, 16), (226, 222, 206))
    d.rectangle([0, 0, 47, 15], outline=(40, 40, 40, 255))
    draw_text(img, "COMPOUND", 8, 2, (30, 30, 30, 255), F3)
    draw_text(img, "14", 18, 8, (20, 120, 30, 255), F3)
    d.rectangle([2, 2, 6, 13], fill=(30, 30, 30, 255))
    d.rectangle([41, 2, 45, 13], fill=(30, 30, 30, 255))
    d.polygon([(4, 4), (6, 10), (2, 10)], fill=(220, 190, 40, 255))
    d.polygon([(43, 4), (45, 10), (41, 10)], fill=(220, 190, 40, 255))
    save(img, "c14label")
    # the radiation trefoil on a yellow drum label, and the drum's own paint
    img = M.painted_metal(seed=seed_of("drum"), base=(206, 170, 40), panel=False, chips=4, under=(90, 84, 70))
    M.grime(img, 0.18, seed=seed_of("drumG"), color=(100, 80, 40), bias="bottom")
    save(img, "drum")
    img = Image.open(os.path.join(TEX, "p-drum.png")).convert("RGBA")
    d = ImageDraw.Draw(img)
    cx, cy = 16, 15
    for k in range(3):
        a0 = -90 + k * 120 - 30
        d.pieslice([cx - 11, cy - 11, cx + 11, cy + 11], a0, a0 + 60, fill=(24, 22, 18, 255))
    d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(206, 170, 40, 255))
    d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(24, 22, 18, 255))
    M.grime(img, 0.1, seed=seed_of("trefoilG"), color=(100, 80, 40))
    save(img, "drumsign")
    img = Image.open(os.path.join(TEX, "p-drum.png")).convert("RGBA")
    M.rust(img, 0.5, seed=seed_of("drumrustR"), color=RUST, dark=RUSTDARK)
    M.drips(img, 4, seed=seed_of("drumrustD"), color=(90, 160, 40), strength=0.5, start=4)
    save(img, "drumrust")
    img = Image.open(os.path.join(TEX, "p-drumsign.png")).convert("RGBA")
    M.rust(img, 0.4, seed=seed_of("drumsignrustR"), color=RUST, dark=RUSTDARK)
    M.drips(img, 3, seed=seed_of("drumsignrustD"), color=(90, 160, 40), strength=0.5, start=26)
    save(img, "drumsignrust")
    img = M.painted_metal(seed=seed_of("drumtop"), base=(196, 162, 40), panel=False, chips=3, under=(90, 84, 70))
    d = ImageDraw.Draw(img)
    d.ellipse([6, 6, 12, 12], fill=(120, 110, 90, 255), outline=(60, 54, 40, 255))
    d.ellipse([22, 20, 26, 24], fill=(120, 110, 90, 255), outline=(60, 54, 40, 255))
    d.ellipse([1, 1, 30, 30], outline=(150, 120, 30, 255))
    save(img, "drumtop")
    # the knives behind glass: rows of blades shining against a dark rusted back
    img = M.noise_hv((40, 32, 28), 3, seed_of("knifeback"), S, mottle=6)
    M.rust(img, 0.4, seed=seed_of("knifebackR"), color=(90, 50, 30), dark=(40, 26, 20))
    d = ImageDraw.Draw(img)
    rng = random.Random(seed_of("knives"))
    for row, y0 in enumerate((2, 12, 22)):
        d.line([0, y0, 31, y0], fill=(70, 70, 72, 255))
        x = 1
        while x < 30:
            kind = rng.choice(("knife", "scalpel", "razor"))
            if kind == "knife":
                d.rectangle([x, y0 + 1, x + 1, y0 + 3], fill=(40, 30, 26, 255))
                d.polygon([(x, y0 + 4), (x + 1, y0 + 4), (x + 1, y0 + 9), (x, y0 + 8)], fill=(214, 220, 226, 255))
                d.point([(x + 1, y0 + 5)], fill=(255, 255, 255, 255))
                x += 3
            elif kind == "scalpel":
                d.line([x, y0 + 1, x, y0 + 6], fill=(170, 176, 180, 255))
                d.point([(x, y0 + 7)], fill=(240, 244, 248, 255))
                x += 2
            else:
                d.rectangle([x, y0 + 2, x + 2, y0 + 4], fill=(200, 206, 212, 255))
                d.point([(x + 1, y0 + 3)], fill=(60, 60, 60, 255))
                x += 4
    blood(img, seed_of("knivesB"), 3)
    save(img, "knives")
    # the medicine cabinet's back wall seen through the glass: shelves of bottles and boxes
    img = M.noise_hv((222, 226, 222), 2, seed_of("cabback"), S, mottle=3)
    save(img, "cabback")
    # instruments: a scalpel blade, syringe barrel, stethoscope tube
    save(M.brushed_metal(seed=seed_of("blade"), base=(222, 228, 234), streak=3, sheen=20), "blade")
    img = M.noise_hv((236, 240, 238), 2, seed_of("syringe"), S, mottle=2)
    for y in range(0, S, 4):
        for x in range(10, 22):
            M.touch(img, x, y, -0.2)
    save(img, "syringe")
    # old surgical equipment casing: cracked cream enamel with a dead dial window
    img = gloss((206, 200, 178), seed_of("oldmachine"))
    d = ImageDraw.Draw(img)
    d.rectangle([4, 4, 18, 13], fill=(30, 34, 32, 255), outline=(90, 90, 80, 255))
    d.line([6, 12, 12, 6], fill=(220, 220, 220, 255))
    for x in (8, 15, 22):
        d.ellipse([x - 2, 19, x + 2, 23], fill=(40, 40, 40, 255))
    d.line([20, 2, 28, 12, 26, 18], fill=(110, 100, 80, 255))
    M.grime(img, 0.25, seed=seed_of("oldmachineG"), color=(120, 100, 70))
    M.rust(img, 0.12, seed=seed_of("oldmachineR"), color=RUST, dark=RUSTDARK)
    save(img, "oldmachine")
    img = M.noise_hv((176, 150, 108), 3, seed_of("cardboard"), S, mottle=6)
    M.grime(img, 0.2, seed=seed_of("cardboardG"), color=(110, 90, 60))
    M.emboss_lines(img, ys=(10,), strength=0.15)
    save(img, "cardboard")
    # a pill bottle label and a bandage roll
    img, d = pic((S, S), (190, 110, 40))
    d.rectangle([0, 10, 31, 22], fill=(240, 238, 228, 255))
    for y in (13, 16, 19):
        d.line([3, y, 26, y], fill=(80, 80, 80, 255))
    save(img, "pillbottle")
    img = M.fabric(seed=seed_of("bandage"), base=(238, 234, 222), weave="basket", contrast=6)
    for y in range(0, S, 5):
        for x in range(S):
            M.touch(img, x, y, -0.1)
    save(img, "bandage")
    img, d = pic((S, S), (236, 236, 232))
    d.rectangle([0, 0, 31, 9], fill=(40, 90, 170, 255))
    draw_text(img, "AMOX", 3, 2, (255, 255, 255, 255), F3)
    d.rectangle([12, 14, 18, 26], fill=(210, 40, 40, 255))
    d.rectangle([9, 17, 21, 23], fill=(210, 40, 40, 255))
    save(img, "pillbox")
    # the ward desk's clipboard sheet, a chart with a red line
    img, d = pic((S, S), (238, 236, 226))
    for y in range(4, 31, 4):
        d.line([2, y, 29, y], fill=(170, 190, 210, 255))
    d.line([(3, 26), (8, 20), (12, 22), (17, 12), (22, 15), (28, 6)], fill=(200, 40, 40, 255))
    save(img, "chart")
    # surgical lamp: the glowing lens (concentric reflector rings), the housing
    img, d = pic((S, S), (238, 244, 250))
    for r, c in ((15, (200, 210, 220)), (12, (250, 252, 255)), (9, (220, 230, 240)), (6, (255, 255, 255)), (3, (210, 220, 230))):
        d.ellipse([16 - r, 16 - r, 15 + r, 15 + r], fill=c + (255,))
    save(img, "lens")
    img = gloss((226, 230, 228), seed_of("lamphead"))
    M.grime(img, 0.12, seed=seed_of("lampheadG"), color=(150, 140, 120))
    specks(img, seed_of("lampheadR"), 3, [RUST], (1, 2))
    save(img, "lamphead")
    # the operating table's pad: black-green vinyl, cracked
    img = M.noise_hv((40, 58, 54), 3, seed_of("optpad"), S, mottle=5)
    M.crack(img, seed_of("optpadC"), strength=0.3)
    M.crack(img, seed_of("optpadC2"), strength=0.25)
    M.stain(img, seed=seed_of("optpadB"), radius=6, color=(60, 10, 10), strength=0.4, at=(10, 20))
    save(img, "optpad")
    # a name card for the crib
    img, d = pic((S, 16), (240, 236, 224))
    d.rectangle([0, 0, 31, 15], outline=(200, 140, 160, 255))
    draw_text(img, "BABY", 6, 2, (170, 70, 100, 255), F3)
    d.line([4, 10, 27, 10], fill=(90, 90, 90, 255))
    save(img, "cribcard")
    # a desk phone's handset coil and the lamp's brass are materials; the reception's sign-in book
    img, d = pic((S, S), (234, 228, 210))
    d.line([16, 0, 16, 31], fill=(150, 140, 120, 255))
    for y in range(4, 30, 3):
        d.line([2, y, 14, y], fill=(150, 160, 190, 255))
        d.line([18, y, 29, y], fill=(150, 160, 190, 255))
    for y in (7, 10, 16):
        d.line([3, y, 3 + (y * 7) % 10, y - 1], fill=(30, 30, 90, 255))
    save(img, "ledger")


def textures():
    WRITTEN.clear()
    metals()
    fabrics()
    woods_and_surfaces()
    glass_and_liquids()
    organic()
    pictures()
    return list(WRITTEN)


if __name__ == "__main__":
    print(len(textures()), "textures")
