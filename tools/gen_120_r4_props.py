"""Level 120 round 4 (the asset-quality pass): the cabinets, desks and the rest of the data hall's furniture, rebuilt as
geometry on matlib materials (see gen_120_r4.py, which runs this). Every block faces north in its shape."""
import math
import random

from PIL import Image, ImageDraw

import matlib as M
from modelkit import box, keypad
from gen_120 import SIDES, ROTATE, METAL, WOOD, STONE, json_block, drops, cuboid, FULL, cube_block
from gen_120_r4 import (b, uvb, shape, save, opaque, hires, text_center, font, px_set, shade3, N_, ALL, rack_elements, GRAPH, OFFW, RED)

SIDED = [{"code": "side", "states": SIDES}]


def sided(code, states_to_base):
    out = {}
    for state, base in states_to_base.items():
        for s in SIDES:
            out[f"{code}-{state}-{s}" if state else f"{code}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    return out


# ======================================================================== Textures

def louvre(base, seed, pitch=4):
    img = M.painted_metal(seed, base=base, panel=False, chips=2)
    for y in range(0, 32, pitch):
        for x in range(32):
            M.touch(img, x, y, 0.22)
            M.touch(img, x, y + 1, -0.1)
            for k in range(2, pitch):
                M.touch(img, x, y + k, -0.55 + 0.1 * k)
    return img


def glass_screen(base, seed, refl=0.18):
    img = M.noise_hv(base, 1, seed, mottle=2)
    for y in range(32):
        for x in range(32):
            d = (x + y - 18) / 6.0
            if -1 < d < 1:
                M.touch(img, x, y, refl * (1 - abs(d)))
            vign = math.hypot((x - 15.5) / 16, (y - 15.5) / 16)
            M.touch(img, x, y, -0.25 * vign)
    return img


def label_tex(lines, bg, fg, w=32, h=32, size=7, border=None):
    def draw(img, d, k):
        if border:
            d.rectangle([0, 0, w * k - 1, h * k - 1], outline=border, width=k)
        n = len(lines)
        for i, line in enumerate(lines):
            text_center(d, (0, i * h * k / n, w * k, (i + 1) * h * k / n), line, size * k, fg)
    return hires(w, h, draw, bg=bg)


def warning_tex():
    """DANGER / HIGH VOLTAGE: a yellow plate, a black triangle with a bolt, the words under it."""
    def draw(img, d, k):
        d.rectangle([0, 0, 32 * k, 32 * k], fill=(214, 176, 40))
        d.rectangle([k, k, 31 * k - 1, 31 * k - 1], outline=(20, 20, 20), width=k)
        d.polygon([(16 * k, 3 * k), (27 * k, 20 * k), (5 * k, 20 * k)], fill=(20, 20, 20))
        d.polygon([(16 * k, 7 * k), (24 * k, 18.5 * k), (8 * k, 18.5 * k)], fill=(214, 176, 40))
        d.polygon([(17 * k, 8 * k), (13 * k, 14 * k), (16 * k, 14 * k), (14.5 * k, 18 * k), (19 * k, 12 * k), (16 * k, 12 * k)], fill=(20, 20, 20))
        text_center(d, (0, 21 * k, 32 * k, 26 * k), "DANGER", 5 * k, (20, 20, 20))
        text_center(d, (0, 26 * k, 32 * k, 31 * k), "480 V", 5 * k, (20, 20, 20))
    img = hires(32, 32, draw)
    return M.grime(img, 0.15, 7701)


def textures():
    rng = random.Random(7700)
    # UPS and tape library: graphite paint, a panelled door face, louvres
    save(M.grime(M.painted_metal(7710, base=GRAPH, panel=False, chips=4, under=(100, 100, 98)), 0.12, 7711, bias="bottom"), "up-paint")
    save(M.grime(M.painted_metal(7712, base=shade3(GRAPH, 1.06), panel=True, chips=3, under=(100, 100, 98)), 0.1, 7713, bias="bottom"), "up-door")
    save(M.grime(louvre(shade3(GRAPH, 1.1), 7714), 0.1, 7715), "up-louvre")
    save(glass_screen((30, 38, 34), 7716), "lcd-dead")
    save(label_tex(["UPS 2", "160 kVA"], (226, 224, 214), (24, 24, 24)), "pl-ups")
    save(label_tex(["CRAC 3"], (226, 224, 214), (24, 24, 24), size=9), "pl-crac")
    save(label_tex(["TAPE", "LIB 1"], (226, 224, 214), (24, 24, 24)), "pl-tape")
    save(label_tex(["BATTERY", "ACID", "NO FLAME"], (214, 176, 40), (20, 20, 20), size=6, border=(20, 20, 20)), "pl-acid")
    save(warning_tex(), "pl-hv")
    save(label_tex(["FM-200", "AGENT"], (228, 226, 216), (150, 30, 26), size=8), "pl-agent")
    # Breakers: black bodies, white toggles
    save(M.rubber(7720, base=(30, 30, 32)), "bk-body")
    save(M.noise_hv((206, 204, 196), 3, 7721, mottle=3), "bk-white")
    # A circuit board: green with traces and chips
    pcb = M.noise_hv((38, 84, 52), 3, 7722, mottle=4)
    p = pcb.load()
    for _ in range(14):
        x, y = rng.randrange(32), rng.randrange(32)
        horiz = rng.random() < 0.5
        for i in range(rng.randint(4, 12)):
            px_set(pcb, x + (i if horiz else 0), y + (0 if horiz else i), (150, 140, 70))
    for _ in range(5):
        x, y = rng.randrange(28), rng.randrange(28)
        for dy in range(3):
            for dx in range(4):
                px_set(pcb, x + dx, y + dy, (22, 22, 24))
    save(pcb, "pcb")
    save(M.noise_hv((60, 70, 96), 3, 7723, mottle=4), "cap-blue")
    # Batteries: matte dark plastic with a pale band; their tops with the vent caps
    bat = M.noise_hv((62, 64, 66), 3, 7724, mottle=3)
    for y in range(6, 11):
        for x in range(32):
            px_set(bat, x, y, M.lift((150, 148, 140), rng.uniform(-3, 3)))
    for x in range(3, 29, 6):
        for y in range(7, 10):
            px_set(bat, x, y, (40, 40, 40))
    save(bat, "bt-case")
    save(M.noise_hv((150, 40, 34), 3, 7725, mottle=3), "term-red")
    # The CRAC: aged off-white enamel, a panelled face, louvres, the coil, the fan, the duct
    cr = M.painted_metal(7730, base=OFFW, panel=False, chips=3, under=(120, 112, 100))
    M.grime(cr, 0.18, 7731, bias="bottom")
    save(cr, "cr-paint")
    crp = M.painted_metal(7732, base=OFFW, panel=True, chips=2, under=(120, 112, 100), screws=True)
    M.grime(crp, 0.16, 7733, bias="bottom")
    M.drips(crp, 2, 7734, color=(130, 92, 56), length=(4, 12), strength=0.3, start=3)
    save(crp, "cr-panel")
    save(M.grime(louvre(shade3(OFFW, 0.96), 7735, pitch=3), 0.2, 7736), "cr-louvre")
    coil = M.brushed_metal(7737, base=(150, 152, 150), direction="v", streak=6)
    for x in range(0, 32, 2):
        for y in range(32):
            M.touch(coil, x, y, -0.3)
    for y in (6, 22):
        for x in range(32):
            px_set(coil, x, y, (150, 92, 60))
    save(M.grime(coil, 0.25, 7738, color=(80, 76, 66)), "cr-coil")
    save(M.rubber(7739, base=(36, 36, 38)), "cr-fan")
    save(M.galvanised(7740, base=(150, 154, 156), spangle=10), "du-galv")
    save(M.brushed_metal(7741, base=(196, 198, 200), streak=10, sheen=14), "du-tape")
    # The desk: a pale grey laminate with wear, a dark edge band, grey steel; the CRT's yellowed plastic and its vents
    top = M.noise_hv((168, 164, 152), 3, 7750, mottle=5)
    M.scratches(top, 5, 7751, light=0.12)
    M.stain(top, 7752, radius=4, color=(120, 100, 70), strength=0.25, at=(22, 9))
    save(top, "dk-top")
    save(M.noise_hv((64, 60, 56), 2, 7753, mottle=2), "dk-edge")
    save(M.grime(M.painted_metal(7754, base=(112, 114, 116), panel=False, chips=3), 0.08, 7755, bias="bottom"), "dk-steel")
    save(M.grime(M.painted_metal(7756, base=(118, 120, 122), panel=True, chips=2), 0.08, 7757), "dk-drawer")
    crt = M.noise_hv((178, 170, 146), 3, 7758, mottle=6)
    M.grime(crt, 0.14, 7759, color=(130, 110, 70))
    save(crt, "crt-beige")
    vent = crt.copy()
    for y in range(2, 30, 3):
        for x in range(4, 28):
            px_set(vent, x, y, (60, 56, 46))
    save(vent, "crt-vent")
    kb = Image.new("RGBA", (32, 32), (88, 84, 74, 255))
    for y in range(0, 32, 2):
        for x in range(0, 32, 2):
            key = (196, 190, 172) if (y // 2) % 6 != 5 else (150, 146, 132)
            if (x // 2 + y // 2) % 11 == 0:
                key = (150, 146, 132)
            px_set(kb, x, y, M.lift(key, rng.uniform(-6, 4)))
    save(kb, "kb-top")
    save(M.fabric(7760, base=(46, 64, 104), weave="plain", contrast=6), "binder")
    # Monitors: black plastic, a dead panel, a glitched one (corrupted frames of a corridor), the arm
    save(M.rubber(7761, base=(30, 30, 32)), "mon-black")
    save(glass_screen((18, 20, 24), 7762, refl=0.22), "mon-dead")
    gl = Image.new("RGBA", (32, 32), (8, 10, 14, 255))
    for y in range(32):
        for x in range(32):
            # a corridor in perspective, broken into shifted bands
            shift = [0, 5, -3, 9, 0, -6, 2, 0][y // 4]
            xx = (x + shift) % 32
            v = 40 + 90 * (1 - abs(xx - 16) / 16) * (1 - abs(y - 16) / 18)
            c = (v * 0.9, v * 0.85, v * 0.45)
            if y // 4 in (1, 5):
                c = (c[2] * 0.6, c[1], c[0] * 1.1)
            if (y % 2) == 0:
                c = shade3(c, 0.7)
            px_set(gl, x, y, c)
    for _ in range(18):
        x, y = rng.randrange(32), rng.randrange(32)
        for dx in range(rng.randint(2, 6)):
            px_set(gl, x + dx, y, rng.choice(((255, 40, 80), (40, 255, 120), (240, 240, 240))))
    save(gl, "mon-glitch")
    save(M.brushed_metal(7763, base=(120, 122, 126), streak=6), "arm-grey")
    # The ladder rack and raceway
    save(M.galvanised(7770, base=(140, 144, 146), spangle=10), "lr-galv")
    fy = M.noise_hv((196, 164, 40), 3, 7771, mottle=4)
    M.grime(fy, 0.15, 7772, color=(90, 80, 50))
    save(fy, "fibre-y")
    # Fire suppression: red cylinders, brass valves, the gauge
    red = M.painted_metal(7780, base=RED, panel=False, chips=4, under=(110, 104, 96))
    M.grime(red, 0.12, 7781, bias="bottom")
    save(red, "fs-red")
    save(M.brushed_metal(7782, base=(176, 146, 80), streak=8, sheen=12), "fs-brass")
    save(label_tex(["0", "  PSI"], (232, 230, 220), (20, 20, 20), size=8, border=(20, 20, 20)), "fs-gauge")
    # The tape library's cartridges: rows of black spines with white and coloured labels
    tl = Image.new("RGBA", (32, 32), (14, 14, 16, 255))
    for row in range(4):
        y0 = row * 8
        for col in range(16):
            x = col * 2
            if rng.random() < 0.12:
                continue  # an empty slot
            for y in range(y0 + 1, y0 + 7):
                px_set(tl, x, y, (36, 36, 40))
            px_set(tl, x, y0 + 2, (220, 218, 208))
            px_set(tl, x, y0 + 3, rng.choice(((60, 90, 170), (170, 60, 50), (60, 140, 70), (200, 180, 60), (220, 218, 208))))
            px_set(tl, x, y0 + 4, (220, 218, 208))
        for x in range(32):
            px_set(tl, x, y0 + 7, (70, 72, 76))
    save(tl, "tl-tapes")
    save(M.glass(7790, base=(150, 170, 176), alpha=255, streaks=1), "glass-shard")


def floor_textures():
    """The raised floor: four 16 px panels a block, each a bevelled steel-cored tile with a dirty white laminate top,
    a dark gap between panels; dirtier, perforated, a grommet, a puddle, a lifted panel."""
    base = (204, 200, 188)

    def panels(seed, grimy=0.12):
        img = M.noise_hv(base, 3, seed, mottle=5)
        for (x0, y0) in ((0, 0), (16, 0), (0, 16), (16, 16)):
            M.bevel(img, (x0, y0, x0 + 15, y0 + 15), 1, 0.14)
            for i in range(16):
                px_set(img, x0 + 15, y0 + i, (92, 90, 84))
                px_set(img, x0 + i, y0 + 15, (92, 90, 84))
        M.grime(img, grimy, seed + 1, color=(110, 100, 82), cells=(8, 4, 2))
        M.scratches(img, 4, seed + 2, light=0.08)
        return img

    save(panels(7800, 0.1), "floor-clean")
    dirty = panels(7802, 0.24)
    M.stain(dirty, 7803, radius=6, color=(120, 104, 80), strength=0.25, at=(9, 22))
    save(dirty, "floor-dirty")
    vent = panels(7804, 0.14)
    for (x0, y0) in ((0, 0), (16, 0), (0, 16), (16, 16)):
        for y in range(y0 + 2, y0 + 14, 2):
            for x in range(x0 + 2 + (y // 2 % 2), x0 + 14, 2):
                px_set(vent, x, y, (34, 34, 36))
                M.touch(vent, x, y + 1, 0.08)
    save(vent, "floor-vent")
    port = panels(7806, 0.14)
    for y in range(20, 27):
        for x in range(4, 12):
            edge = y in (20, 26) or x in (4, 11)
            px_set(port, x, y, (40, 40, 42) if edge else ((14, 14, 16) if (x + y) % 2 else (28, 28, 30)))
    for y in range(21, 26):
        px_set(port, 7, y, (54, 70, 104))
    save(port, "floor-port")
    wet = panels(7808, 0.16)
    M.stain(wet, 7809, radius=9, color=(96, 92, 84), strength=0.45, at=(15, 15), ring=0.7)
    for (x, y) in ((11, 12), (12, 12), (17, 18), (18, 18), (13, 19)):
        M.touch(wet, x, y, 0.3)
    save(wet, "floor-wet")
    hole = panels(7810, 0.16)
    for y in range(16, 32):
        for x in range(0, 16):
            px_set(hole, x, y, (22, 22, 24))
    save(hole, "floor-hole")


# ======================================================================== Shapes

def cyl(name, cx, cz, y0, y1, r, tex, faces=("north", "east", "south", "west", "up", "down")):
    """A round-ish upright: two crossed boxes and one turned 45 degrees (an octagon in plan)."""
    s = r * 0.42
    return [b(name + "A", (cx - r, y0, cz - s), (cx + r, y1, cz + s), tex, faces=faces),
            b(name + "B", (cx - s, y0 + 0.01, cz - r), (cx + s, y1 - 0.01, cz + r), tex, faces=faces),
            b(name + "C", (cx - r * 0.98, y0 + 0.02, cz - s), (cx + r * 0.98, y1 - 0.02, cz + s), tex, faces=faces, rot=(0, 45, 0), origin=(cx, y0, cz))]


def hollow(x0, y0, z0, x1, y1, z1, tex="rk-void"):
    """The inside of an open cabinet seen through its front: its back, sides, floor and roof facing inward."""
    t = 0.05
    return [b("InBack", (x0, y0, z1 - t), (x1, y1, z1), tex, faces=N_),
            b("InW", (x0, y0, z0), (x0 + t, y1, z1), tex, faces=("east",)),
            b("InE", (x1 - t, y0, z0), (x1, y1, z1), tex, faces=("west",)),
            b("InFloor", (x0, y0, z0), (x1, y0 + t, z1), tex, faces=("up",)),
            b("InRoof", (x0, y1 - t, z0), (x1, y1, z1), tex, faces=("down",))]


def cabinet_shell(paint, door, y0, y1, plinth, cap):
    """A floor cabinet's carcass, 1 to 15 wide, 1.5 to 15.5 deep, its front a door face at z 1.5 (handles go before it)."""
    els = [b("Body", (1, y0, 1.5), (15, y1, 15.5), {"front": door, "side": paint, "back": paint, "top": paint, "bottom": paint},
             faces=("north", "east", "west", "south"))]
    if plinth:
        els.append(b("Plinth", (1.25, 0, 1.75), (14.75, 1, 15.25), "rk-black", faces=("north", "east", "west", "south")))
        els[0]["from"][1] = 1
    if cap:
        els.append(b("Cap", (0.75, y1 - 0.75, 1.25), (15.25, y1, 15.75), paint, faces=ALL))
    return els


def ups_elements(part, state):
    lower, open_ = part == "lower", state == "open"
    if lower:
        els = cabinet_shell("up-paint", "up-door", 0, 16, True, False)
        if not open_:
            els += [b("Louvre", (2.5, 2, 1.0), (13.5, 7, 1.5), "up-louvre", faces=("north", "up", "east", "west")),
                    b("Seam", (7.85, 1, 1.35), (8.15, 16, 1.5), "rk-black", faces=N_),
                    b("HandleL", (6.6, 9, 0.6), (7.2, 13.5, 1.5), "rk-chrome", faces=("north", "east", "west", "up", "down")),
                    b("HandleR", (8.8, 9, 0.6), (9.4, 13.5, 1.5), "rk-chrome", faces=("north", "east", "west", "up", "down"))]
        else:
            # The door is off: the battery trays inside, the door leaning on the cabinet's foot
            els[0]["faces"].pop("north")
            els += hollow(1.1, 1, 1.5, 14.9, 16, 15.4)
            for i, y in enumerate((1.5, 6.5, 11.5)):
                els.append(b(f"Tray{i}", (1.5, y, 2.5), (14.5, y + 0.5, 14), "dk-steel", faces=("north", "up")))
                for j in range(4):
                    x = 2 + j * 3.2
                    els.append(b(f"Bat{i}{j}", (x, y + 0.5, 3.5), (x + 2.8, y + 4, 13), {"front": "bt-case", "side": "bt-case", "top": "rk-black"},
                                 faces=("north", "up", "east", "west")))
                    els.append(b(f"T{i}{j}", (x + 0.4, y + 4, 4), (x + 1, y + 4.5, 4.6), "term-red", faces=("north", "up", "east", "west")))
            els.append(b("Door", (1.5, 0, -2.5), (14.5, 15, -1.75), {"front": "up-door", "back": "up-paint", "side": "up-paint", "top": "up-paint"},
                         faces=("north", "south", "east", "west", "up"), rot=(-16, 0, 0), origin=(8, 0, -2.1)))
            els.append(b("DoorLouvre", (2.5, 2, -3.0), (13.5, 7, -2.5), "up-louvre", faces=("north", "up"), rot=(-16, 0, 0), origin=(8, 0, -2.1)))
            els.append(b("Cable", (6, 0, -1.5), (6.6, 0.5, 2.5), "cb-black", faces=("up", "east", "west")))
        return els
    els = cabinet_shell("up-paint", "up-door", 0, 15, False, True)
    if not open_:
        els += [
            # The display and its keypad, the status bar, the plates; the breaker window below them
            b("LcdBezel", (3, 10, 1.1), (9, 13.5, 1.5), "rk-black", faces=("north", "east", "west", "up", "down")),
            uvb("Lcd", (3.5, 10.5, 1.0), (8.5, 13, 1.1), "lcd-dead", (0, 0, 16, 16)),
            *keypad("Keys", 9.5, 10, 1.5, cols=3, rows=2, key=0.75, gap=0.5, plate="rk-black", keys="bk-white"),
            uvb("Plate", (3, 13.6, 1.3), (7, 14.6, 1.5), "pl-ups", (0, 3, 16, 7)),
            uvb("Hv", (11.5, 12.75, 1.3), (14, 14.25, 1.5), "pl-hv", (0, 0, 16, 16)),
            b("BkFrame", (2.5, 3, 1.0), (13.5, 8.5, 1.5), "rk-black", faces=("north", "up", "down", "east", "west")),
            b("BkInside", (3, 3.5, 0.95), (13, 8, 1.0), "rk-void", faces=N_),
            b("Seam", (7.85, 0, 1.35), (8.15, 2.5, 1.5), "rk-black", faces=N_),
        ]
        rng = random.Random("breakers")
        for i in range(8):
            x = 3.4 + i * 1.2
            els.append(b(f"Bk{i}", (x, 4, 0.5), (x + 1, 7.5, 0.95), "bk-body", faces=("north", "up", "east", "west")))
            up = rng.random() < 0.6
            els.append(b(f"Tg{i}", (x + 0.3, 6.0 if up else 4.6, 0.2), (x + 0.7, 7.0 if up else 5.6, 0.5), "bk-white", faces=("north", "up", "east", "west", "down")))
    else:
        els[0]["faces"].pop("north")
        els += hollow(1.1, 0, 1.5, 14.9, 14.25, 15.4)
        els += [b("Board", (2, 5, 9), (14, 13.5, 9.5), "pcb", faces=N_),
                b("CapA", (3, 1, 6), (5, 4.5, 8), "cap-blue", faces=("north", "up", "east", "west")),
                b("CapB", (5.5, 1, 6), (7.5, 4.5, 8), "cap-blue", faces=("north", "up", "east", "west")),
                b("Heatsink", (9, 1, 5), (13.5, 4, 9), "du-galv", faces=("north", "up", "east", "west")),
                b("BusBar", (2, 13.6, 4), (14, 14.2, 9), "fs-brass", faces=("north", "down", "up")),
                b("Wires", (11, 4, 4), (11.6, 13.5, 4.6), "cb-red", faces=("north", "east", "west")),
                # Its door hanging off the top hinge
                b("Door", (1.5, 0.5, 0.75), (14.5, 14, 1.4), {"front": "up-door", "back": "up-paint", "side": "up-paint"},
                  faces=("north", "south", "east", "west", "down"), rot=(0, -58, 0), origin=(14.5, 7, 1.0))]
    return els


def battery_elements(part):
    lower = part == "lower"
    els = [b("Back", (1, 0, 14.5), (15, 16 if lower else 14, 15.5), "up-paint", faces=("north", "south")),
           b("SideW", (1, 0, 1.5), (1.75, 16 if lower else 14, 14.5), "up-paint", faces=("west", "north", "east")),
           b("SideE", (14.25, 0, 1.5), (15, 16 if lower else 14, 14.5), "up-paint", faces=("east", "north", "west"))]
    if lower:
        els.append(b("Plinth", (1.25, 0, 2), (14.75, 1, 14.5), "rk-black", faces=("north",)))
    else:
        els.append(b("Cap", (0.75, 13.25, 1.25), (15.25, 14, 15.75), "up-paint", faces=ALL))
        els.append(uvb("Acid", (5, 11, 1.2), (11, 13, 1.35), "pl-acid", (0, 0, 16, 16)))
    shelves = (1.0, 6.0, 11.0) if lower else (0.0, 5.0)
    for i, y in enumerate(shelves):
        els.append(b(f"Shelf{i}", (1.75, y, 2), (14.25, y + 0.5, 14.5), "dk-steel", faces=("north", "up")))
        for j in range(3):
            x = 2.2 + j * 4.0
            els.append(b(f"Bat{i}{j}", (x, y + 0.5, 3), (x + 3.6, y + 4.2, 14), {"front": "bt-case", "side": "bt-case", "top": "rk-black"},
                         faces=("north", "up", "east", "west")))
            els.append(b(f"Tp{i}{j}", (x + 0.4, y + 4.2, 3.6), (x + 1.1, y + 4.6, 4.3), "term-red", faces=("north", "up", "east", "west")))
            els.append(b(f"Tn{i}{j}", (x + 2.5, y + 4.2, 3.6), (x + 3.2, y + 4.6, 4.3), "rk-black", faces=("north", "up", "east", "west")))
        els.append(b(f"Link{i}", (2.9, y + 4.6, 3.8), (13.4, y + 4.9, 4.2), "fs-brass", faces=("north", "up")))
    # (No door: an open battery rack, a restraint bar across each shelf, the uprights at the front)
    top = 16 if lower else 13.25
    els += [b("UpL", (1.5, 0, 1.25), (2.25, top, 2), "dk-steel", faces=("north", "east", "west")),
            b("UpR", (13.75, 0, 1.25), (14.5, top, 2), "dk-steel", faces=("north", "east", "west"))]
    for i, y in enumerate(shelves):
        els.append(b(f"Rail{i}", (2.25, y + 2.2, 1.6), (13.75, y + 2.7, 2.0), "rk-black", faces=("north", "up", "down")))
    return els


def crac_elements(part):
    if part == "duct":
        return [b("Duct", (3, 0, 4), (13, 16, 13), "du-galv", faces=("north", "east", "south", "west")),
                b("FlangeB", (2.5, 0, 3.5), (13.5, 0.75, 13.5), "du-galv", faces=("north", "east", "south", "west", "up")),
                b("FlangeT", (2.5, 15.25, 3.5), (13.5, 16, 13.5), "du-galv", faces=("north", "east", "south", "west", "down")),
                b("Tape", (2.95, 7, 3.95), (13.05, 8.5, 13.05), "du-tape", faces=("north", "east", "south", "west")),
                b("Damper", (7.5, 9.5, 3.4), (8.5, 10.5, 4), "rk-black", faces=("north", "east", "west", "up")),
                b("DamperArm", (6, 9.75, 3.2), (10, 10.25, 3.45), "rk-chrome", faces=("north", "up", "down"))]
    els = [b("Body", (0.5, 0, 2), (15.5, 16, 15.5), {"front": "cr-panel", "side": "cr-panel", "back": "cr-paint", "top": "cr-paint", "bottom": "cr-paint"},
             faces=("north", "east", "west", "south"))]
    if part in ("lower", "loweropen"):
        els[0]["from"][1] = 1
        els.append(b("Plinth", (0.75, 0, 2.25), (15.25, 1, 15.25), "rk-black", faces=("north", "east", "west", "south")))
        if part == "lower":
            els += [b("Louvre", (1.5, 1.5, 1.5), (14.5, 9, 2), "cr-louvre", faces=("north", "up", "east", "west")),
                    b("PanelU", (1.5, 9.5, 1.5), (14.5, 16, 2), "cr-panel", faces=("north", "up", "down", "east", "west")),
                    b("LatchA", (2.5, 12, 1.0), (3.5, 13.5, 1.5), "rk-black", faces=("north", "east", "west", "up", "down")),
                    b("LatchB", (12.5, 12, 1.0), (13.5, 13.5, 1.5), "rk-black", faces=("north", "east", "west", "up", "down"))]
        else:
            # The front panel off and leaning against it: the fans and the coil behind
            els[0]["faces"].pop("north")
            els += hollow(0.6, 1, 2, 15.4, 16, 15.4)
            els += [b("Coil", (1, 1, 11), (15, 15.5, 12), "cr-coil", faces=N_)]
            for i, x in enumerate((4.5, 11.5)):
                els += [b(f"FanRing{i}", (x - 3, 3, 6), (x + 3, 9, 7), "cr-fan", faces=("north",)),
                        b(f"Blade{i}a", (x - 2.6, 5.7, 5.8), (x + 2.6, 6.3, 6), "cr-fan", faces=("north",), rot=(0, 0, 30), origin=(x, 6, 5.9)),
                        b(f"Blade{i}b", (x - 2.6, 5.7, 5.7), (x + 2.6, 6.3, 5.9), "cr-fan", faces=("north",), rot=(0, 0, -50), origin=(x, 6, 5.8)),
                        b(f"Hub{i}", (x - 0.75, 5.25, 5.4), (x + 0.75, 6.75, 5.8), "du-galv", faces=("north", "east", "west", "up", "down"))]
            els += [b("Motor", (6.5, 10, 6), (9.5, 14, 10), "dk-steel", faces=("north", "east", "west", "up")),
                    b("Panel", (1, 0, -3.5), (15, 13, -2.75), {"front": "cr-louvre", "back": "cr-paint", "side": "cr-paint", "top": "cr-paint"},
                      faces=("north", "south", "east", "west", "up"), rot=(-18, 0, 0), origin=(8, 0, -3.1))]
        return els
    # Upper: the control panel with its display and buttons, the plate, the top grille and the duct's collar
    els += [b("PanelU", (1.5, 0, 1.5), (14.5, 14.5, 2), "cr-panel", faces=("north", "up", "east", "west")),
            b("Ctl", (3, 7, 1.0), (13, 12.5, 1.5), "dk-steel", faces=("north", "east", "west", "up", "down")),
            uvb("Lcd", (3.75, 8.5, 0.9), (8.5, 11.75, 1.0), "lcd-dead", (0, 0, 16, 16)),
            uvb("Plate", (5, 2.5, 1.3), (11, 4.5, 1.5), "pl-crac", (0, 4, 16, 11)),
            b("Cap", (0.25, 15, 1.75), (15.75, 16, 15.75), "cr-paint", faces=ALL),
            b("Collar", (2.5, 16, 3.5), (13.5, 16.5, 13.5), "du-galv", faces=("north", "east", "south", "west", "up"))]
    for i in range(3):
        x = 9.5 + i * 1.2
        els.append(b(f"Btn{i}", (x, 9, 0.6), (x + 0.8, 9.8, 1.0), "bk-white" if i else "term-red", faces=("north", "east", "west", "up", "down")))
    els.append(b("Status", (9.5, 11, 0.8), (13, 11.5, 1.0), "rk-led-dead", faces=N_))
    return els


def desk_elements(drawers=True):
    """An operator's desk, 0.72 high, its user to the north: a laminate top with a dark edge band, a leg panel at the
    left, a drawer pedestal at the right, a modesty panel at the back, a cable grommet."""
    els = [b("Top", (0.25, 10.75, 0.75), (15.75, 11.5, 15.25), {"top": "dk-top", "side": "dk-edge", "bottom": "dk-steel"}, faces=ALL),
           b("LegL", (0.75, 0, 1.5), (1.75, 10.75, 14.5), "dk-steel", faces=("north", "east", "west", "south")),
           b("Modesty", (1.75, 3.5, 13.5), (15, 10.75, 14), "dk-steel", faces=("north", "south")),
           b("Grommet", (12, 11.5, 12.5), (14, 11.55, 14), "rk-black", faces=("up",))]
    if drawers:
        els += [b("Ped", (10.5, 0.5, 1.25), (15.25, 10.75, 13.5), {"front": "dk-steel", "side": "dk-steel"}, faces=("north", "east", "west")),
                b("Kick", (10.75, 0, 1.5), (15, 0.5, 13), "rk-black", faces=("north",))]
        for i, (y0, y1) in enumerate(((0.75, 4.75), (5, 7.75), (8, 10.5))):
            els.append(b(f"Drawer{i}", (10.75, y0, 0.9), (15, y1, 1.25), "dk-drawer", faces=("north", "up", "down", "east", "west")))
            els.append(b(f"Pull{i}", (12, y1 - 1.0, 0.6), (13.75, y1 - 0.6, 0.9), "rk-chrome", faces=("north", "up", "down", "east", "west")))
        # (one drawer left a little open)
        els[-2]["from"][2] -= 2.0
        els[-2]["to"][2] -= 2.0
        els[-1]["from"][2] -= 2.0
        els[-1]["to"][2] -= 2.0
    else:
        els.append(b("LegR", (14.25, 0, 1.5), (15.25, 10.75, 14.5), "dk-steel", faces=("north", "east", "west", "south")))
    return els


def terminal_elements(state):
    screen = {"dead": "screen-dead", "smashed": "screen-smashed", "boot": "screen-boot"}[state]
    els = desk_elements()
    crt = [
        b("Stand", (5.5, 11.5, 5), (10.5, 11.9, 10), "crt-beige", faces=("north", "east", "west", "south", "up")),
        b("Bezel", (3, 11.9, 3.5), (13, 16, 5), {"front": "crt-beige", "side": "crt-beige", "top": "crt-vent", "back": "crt-beige"}, faces=("east", "west", "up", "down")),
        b("BezelL", (3, 11.9, 3.0), (4.25, 16, 3.5), "crt-beige", faces=("north", "east", "west", "up")),
        b("BezelR", (11.75, 11.9, 3.0), (13, 16, 3.5), "crt-beige", faces=("north", "east", "west", "up")),
        b("BezelT", (4.25, 15.0, 3.0), (11.75, 16, 3.5), "crt-beige", faces=("north", "up", "down")),
        b("BezelB", (4.25, 11.9, 3.0), (11.75, 12.75, 3.5), "crt-beige", faces=("north", "up")),
        uvb("Screen", (4.25, 12.75, 3.4), (11.75, 15.0, 3.5), screen, (0, 0, 16, 6), glow=230 if state == "boot" else 0),
        b("Back1", (3.75, 12.25, 5), (12.25, 15.6, 8.5), {"side": "crt-vent", "top": "crt-vent", "back": "crt-beige"}, faces=("east", "west", "up", "south")),
        b("Back2", (5, 12.75, 8.5), (11, 15.0, 11.5), {"side": "crt-vent", "top": "crt-vent", "back": "crt-beige"}, faces=("east", "west", "up", "south")),
        b("Badge", (5, 12.1, 2.95), (6.5, 12.4, 3.0), "rk-chrome", faces=N_),
        b("Power", (10.5, 12.0, 2.9), (11.2, 12.5, 3.0), "rk-black", faces=N_),
    ]
    if state == "smashed":
        for e in crt:
            e["rotationOrigin"] = [8, 11.9, 7]
            e["rotationY"] = 14
        crt += [b("Shard0", (5, 11.5, 1.2), (6.2, 11.6, 2.0), "glass-shard", faces=("up",), rot=(0, 25, 0)),
                b("Shard1", (8.6, 11.5, 0.9), (10.0, 11.6, 1.6), "glass-shard", faces=("up",), rot=(0, -15, 0))]
    els += crt
    els += [
        uvb("Keyboard", (3.5, 11.5, 0.9), (12, 11.95, 3.1), "kb-top", (0, 0, 8.5, 2.2), faces=("north", "east", "west")),
        b("KeyboardTop", (3.5, 11.5, 0.9), (12, 11.95, 3.1), "kb-top", faces=("up",), uv=(0, 0, 8.5, 2.2)),
        b("Mouse", (13, 11.5, 1.5), (13.9, 11.85, 2.9), "crt-beige", faces=("north", "east", "west", "up", "south")),
        b("Cord", (13.35, 11.5, 2.9), (13.55, 11.6, 6), "cb-grey", faces=("up", "east", "west")),
        b("Binder", (0.8, 11.5, 6), (3.0, 12.2, 10.5), "binder", faces=("north", "east", "west", "up", "south"), rot=(0, 8, 0)),
    ]
    return els


def console_elements(state):
    """An operator's desk with two flat monitors on a pole arm clamped to its back edge."""
    els = desk_elements()
    els += [b("Clamp", (7.4, 10.0, 14.5), (8.6, 12.25, 15.75), "mon-black", faces=("north", "east", "west", "south", "up")),
            b("Pole", (7.7, 12.25, 14.8), (8.3, 15.8, 15.4), "arm-grey", faces=("north", "east", "west", "south", "up"))]
    for i, (sx, glitch) in enumerate(((-1, False), (1, state == "glitch"))):
        cx = 8 + sx * 3.9
        rot = -sx * 14
        mon = [b(f"Mon{i}", (cx - 3.6, 11.9, 7.2), (cx + 3.6, 16, 7.8), "mon-black", faces=("north", "east", "west", "up", "down", "south")),
               uvb(f"Panel{i}", (cx - 3.3, 12.3, 7.1), (cx + 3.3, 15.7, 7.2), "mon-glitch" if glitch else "mon-dead", (0, 2, 16, 10),
                   glow=150 if glitch else 0),
               b(f"Vesa{i}", (cx - 1, 13, 7.8), (cx + 1, 15, 8.4), "mon-black", faces=("east", "west", "up", "down", "south"))]
        for e in mon:
            e["rotationOrigin"] = [cx, 12, 7.8]
            e["rotationY"] = rot
        els += mon
        # The arm: from the pole to the monitor's back, turned in plan
        ax, az = cx, 8.1
        dx, dz = 8 - ax, 15.1 - az
        ln = math.hypot(dx, dz)
        ang = math.degrees(math.atan2(dz, dx))
        els.append(b(f"Arm{i}", (ax, 14.0, az - 0.3), (ax + ln, 14.6, az + 0.3), "arm-grey", faces=("north", "south", "up", "down", "east", "west"),
                     rot=(0, -ang, 0), origin=(ax, 14.3, az)))
        els[-1]["faces"]["up"]["uv"] = [0, 0, 16, 0.6]
    els += [
        b("Keyboard", (4, 11.5, 1.0), (12, 11.9, 3.2), "kb-top", faces=("up",), uv=(0, 0, 8, 2.2)),
        b("KeyboardSide", (4, 11.5, 1.0), (12, 11.9, 3.2), "mon-black", faces=("north", "east", "west")),
        b("Mouse", (13, 11.5, 1.6), (13.9, 11.85, 3.0), "mon-black", faces=("north", "east", "west", "up", "south")),
        b("Mug", (1.5, 11.5, 2.5), (2.6, 12.9, 3.6), "bk-white", faces=("north", "east", "west", "south", "up")),
        b("MugIn", (1.7, 12.9, 2.7), (2.4, 12.95, 3.4), "rk-black", faces=("up",)),
        b("Papers", (1, 11.5, 5), (4.5, 11.6, 9.5), "paper-sheet", faces=("up",), uv=(0, 0, 16, 16), rot=(0, -12, 0)),
    ]
    return els


def tray_elements():
    """A ladder rack along x under the ceiling, on two trapeze hangers: stringers, rungs, cable looms tied on it, the
    yellow fibre raceway alongside."""
    els = [b("StrN", (0, 12, 4.5), (16, 13.5, 5), "lr-galv", faces=("north", "south", "up", "down")),
           b("StrS", (0, 12, 11), (16, 13.5, 11.5), "lr-galv", faces=("north", "south", "up", "down"))]
    for i, x in enumerate((1.5, 5.5, 9.5, 13.5)):
        els.append(b(f"Rung{i}", (x, 12, 5), (x + 1, 12.5, 11), "lr-galv", faces=("up", "down", "east", "west")))
    for i, x in enumerate((2, 13.5)):
        els += [b(f"Rod{i}N", (x, 11.5, 3.6), (x + 0.5, 16, 4.1), "lr-galv", faces=("north", "east", "south", "west")),
                b(f"Rod{i}S", (x, 11.5, 11.9), (x + 0.5, 16, 12.4), "lr-galv", faces=("north", "east", "south", "west")),
                b(f"Strut{i}", (x - 0.25, 11.25, 3.4), (x + 0.75, 12, 12.6), "lr-galv", faces=("north", "south", "east", "west", "down"))]
    for j, (t, z0, z1, h) in enumerate((("cb-blue", 5.2, 7.0, 1.5), ("cb-grey", 7.2, 8.8, 1.2), ("cb-black", 9.0, 10.8, 1.7))):
        els.append(b(f"Loom{j}", (0, 12.5, z0), (16, 12.5 + h, z1), t, faces=("up", "north", "south"), uv=None))
        for k, x in enumerate((3.5, 11.5)):
            els.append(b(f"Tie{j}{k}", (x, 12.45, z0 - 0.1), (x + 0.4, 12.55 + h, z1 + 0.1), "rk-black", faces=("up", "north", "south", "east", "west")))
    # The fibre raceway: a yellow U-channel on its own brackets at the north side
    els += [b("FibreFloor", (0, 13.6, 0.75), (16, 14, 3.25), "fibre-y", faces=("up", "down", "north", "south")),
            b("FibreN", (0, 14, 0.75), (16, 15.25, 1.0), "fibre-y", faces=("north", "south", "up")),
            b("FibreS", (0, 14, 3.0), (16, 15.25, 3.25), "fibre-y", faces=("north", "south", "up")),
            b("FibreCable", (0, 14, 1.25), (16, 14.6, 2.75), "cb-yellow", faces=("up",)),
            b("FibreBkt", (6, 13.3, 0.5), (7, 13.6, 4.2), "lr-galv", faces=("down", "north", "east", "west"))]
    return els


def kvm_elements():
    els = []
    for i, (x, z) in enumerate(((2, 3), (13, 3), (2, 12), (13, 12))):
        els += [b(f"Post{i}", (x, 1.75, z), (x + 0.75, 11, z + 0.75), "rk-chrome", faces=("north", "east", "south", "west")),
                b(f"Fork{i}", (x - 0.1, 1.25, z - 0.1), (x + 0.85, 1.75, z + 0.85), "rk-black", faces=("north", "east", "south", "west", "down")),
                b(f"Wheel{i}", (x + 0.05, 0, z - 0.5), (x + 0.7, 1.25, z + 1.25), "rk-black", faces=("north", "east", "south", "west"))]
    els += [b("Low", (2, 3, 3), (13.75, 3.5, 12.75), "dk-steel", faces=("up", "down", "north", "south", "east", "west")),
            b("LowLipN", (2, 3.5, 3), (13.75, 4, 3.4), "dk-steel", faces=("north", "up", "south")),
            b("Top", (2, 10.5, 3), (13.75, 11, 12.75), "dk-steel", faces=("up", "down", "north", "south", "east", "west")),
            b("HandleL", (2, 11, 12), (2.75, 15, 12.75), "rk-chrome", faces=("north", "east", "south", "west")),
            b("HandleR", (13, 11, 12), (13.75, 15, 12.75), "rk-chrome", faces=("north", "east", "south", "west")),
            b("HandleBar", (2, 15, 12), (13.75, 15.75, 12.75), "rk-black", faces=ALL),
            # The monitor on its post, the keyboard, a box below, the cable trailing
            b("MonPost", (7.5, 11, 9), (8.5, 12.5, 10), "mon-black", faces=("north", "east", "west", "south")),
            b("MonFoot", (6, 11, 8), (10, 11.3, 11), "mon-black", faces=("up", "north", "east", "west", "south")),
            b("Mon", (4, 12, 9.2), (12, 16, 10), "mon-black", faces=("north", "east", "west", "up", "south")),
            uvb("Panel", (4.3, 12.3, 9.1), (11.7, 15.7, 9.2), "mon-dead", (0, 2, 16, 10)),
            b("Keyboard", (4, 11, 3.5), (12, 11.4, 6.5), "kb-top", faces=("up",), uv=(0, 0, 8, 3)),
            b("KeyboardSide", (4, 11, 3.5), (12, 11.4, 6.5), "mon-black", faces=("north", "east", "west")),
            b("Box", (3, 3.5, 4), (9.5, 7.5, 11.5), "box-cardboard", faces=("north", "east", "west", "up", "south")),
            b("Drive", (10, 3.5, 5), (13, 4.5, 9), "rk-black", faces=("north", "east", "west", "up")),
            b("CableA", (7.7, 0, 0), (8.2, 0.4, 3), "cb-black", faces=("up", "east", "west", "north")),
            b("CableB", (7.7, 0.4, 2.6), (8.2, 3, 3.1), "cb-black", faces=("north", "east", "west")),
            b("CableC", (6.5, 0, -6), (7.0, 0.4, 0.2), "cb-black", faces=("up", "east", "west", "north"), rot=(0, 20, 0), origin=(7.95, 0, 0))]
    return els


def firesup_elements(part):
    """The suppression bank against a wall (the wall south): uprights of strut channel, three red cylinders strapped to
    them; above, their valve heads, flex hoses up to the manifold, and the discharge pipe; the pipe alone into the ceiling."""
    xs = (3.25, 8, 12.75)
    if part == "pipe":
        return [b("Pipe", (7.4, 0, 12.4), (8.6, 16, 13.6), "fs-red", faces=("north", "east", "south", "west")),
                b("Clamp", (7.1, 10, 12.1), (8.9, 10.8, 15.9), "lr-galv", faces=("north", "east", "west", "up", "down")),
                b("Nozzle", (7.2, 15.2, 12.2), (8.8, 16, 13.8), "fs-brass", faces=("north", "east", "south", "west"))]
    els = [b("StrutW", (0.5, 0, 14), (1.75, 16, 15.25), "lr-galv", faces=("north", "east", "west")),
           b("StrutE", (14.25, 0, 14), (15.5, 16, 15.25), "lr-galv", faces=("north", "east", "west"))]
    if part == "lower":
        for i, x in enumerate(xs):
            els += cyl(f"Cyl{i}", x, 10.5, 0.25, 16, 2.25, "fs-red", faces=("north", "east", "south", "west"))
            els.append(b(f"Foot{i}", (x - 2.4, 0, 8.2), (x + 2.4, 0.4, 12.8), "rk-black", faces=("north", "east", "west", "up")))
            els.append(uvb(f"Label{i}", (x - 1.4, 7, 8.15), (x + 1.4, 10, 8.2), "pl-agent", (0, 2, 16, 14)))
        els.append(b("Strap", (1.75, 12, 7.9), (14.25, 13, 8.2), "lr-galv", faces=("north", "up", "down")))
        els.append(b("StrapLo", (1.75, 3, 7.9), (14.25, 3.8, 8.2), "lr-galv", faces=("north", "up", "down")))
        return els
    for i, x in enumerate(xs):
        els += cyl(f"Sh{i}", x, 10.5, 0, 1.5, 1.8, "fs-red", faces=("north", "east", "south", "west", "up"))
        els += cyl(f"Neck{i}", x, 10.5, 1.5, 2.5, 0.8, "fs-brass", faces=("north", "east", "south", "west"))
        els += [b(f"Valve{i}", (x - 1.2, 2.5, 9.3), (x + 1.2, 4.5, 11.7), "fs-brass", faces=("north", "east", "south", "west", "up")),
                b(f"Act{i}", (x - 0.8, 4.5, 9.7), (x + 0.8, 5.5, 11.3), "fs-red", faces=("north", "east", "south", "west", "up")),
                uvb(f"Gauge{i}", (x - 0.75, 2.8, 9.2), (x + 0.75, 4.2, 9.3), "fs-gauge", (0, 0, 16, 16)),
                b(f"Hose{i}", (x - 0.3, 4.5, 11.7), (x + 0.3, 9, 12.3), "cb-black", faces=("north", "east", "west", "south"))]
    els += [b("Manifold", (2.5, 9, 12.4), (13.5, 10.2, 13.6), "fs-red", faces=("north", "east", "west", "up", "down", "south")),
            b("Riser", (7.4, 10.2, 12.4), (8.6, 16, 13.6), "fs-red", faces=("north", "east", "south", "west")),
            b("Strap", (1.75, 0.5, 8.4), (14.25, 1.2, 8.7), "lr-galv", faces=("north", "up", "down"))]
    return els


def tapelib_elements(part):
    lower = part == "lower"
    els = cabinet_shell("up-paint", "up-door", 0, 16 if lower else 15, lower, not lower)
    els[0]["faces"]["north"]["texture"] = "#up-paint"
    # The window, the full height of both blocks: its bezel, the tapes in their slots on the back wall, the robot
    wy0, wy1 = (4, 16) if lower else (0, 12)
    els += [b("WinL", (2, wy0, 1.0), (3, wy1, 1.5), "rk-black", faces=("north", "east", "up", "down")),
            b("WinR", (11, wy0, 1.0), (12, wy1, 1.5), "rk-black", faces=("north", "west", "up", "down")),
            uvb("Tapes", (3, wy0, 10.4), (11, wy1, 10.5), "tl-tapes", (0, 0, 8, wy1 - wy0)),
            b("SideTapes", (3, wy0, 2), (3.2, wy1, 10.4), "tl-tapes", faces=("east",)),
            b("Gantry", (6.75, wy0, 6), (7.25, wy1, 6.5), "rk-chrome", faces=("north", "east", "west"))]
    # (the window runs through both blocks: no roof to the lower's inside, no floor to the upper's)
    els += [e for e in hollow(3, wy0, 1.5, 11, wy1, 10.5) if e["name"] != ("InRoof" if lower else "InFloor")]
    # (the window's inside is open: the cabinet's front face only round it)
    els[0]["faces"].pop("north")
    els += [b("FrontL", (1, 1 if lower else 0, 1.5), (2, 16 if lower else 15, 1.6), "up-door", faces=N_),
            b("FrontR", (12, 1 if lower else 0, 1.5), (15, 16 if lower else 15, 1.6), "up-door", faces=N_)]
    if lower:
        els += [b("WinB", (2, 3, 1.0), (12, 4, 1.5), "rk-black", faces=("north", "up")),
                b("FrontB", (2, 1, 1.5), (12, 3, 1.6), "up-louvre", faces=N_),
                b("Shard0", (3, 4, 1.2), (5, 6, 1.3), "glass-shard", faces=N_, rot=(0, 0, 25)),
                b("Shard1", (9, 4, 1.2), (11, 5, 1.3), "glass-shard", faces=N_, rot=(0, 0, -15)),
                b("Glass", (4, 0, -1.5), (6, 0.1, 0.5), "glass-shard", faces=("up",), rot=(0, 30, 0)),
                b("Mail", (12.5, 6, 0.9), (14.5, 8, 1.5), "rk-black", faces=("north", "up", "east", "west")),
                b("Cart", (4, 5.5, 2.5), (6, 9.5, 4.5), "tl-tapes", faces=("north", "east", "west", "up"))]
    else:
        els += [b("WinT", (2, 12, 1.0), (12, 13, 1.5), "rk-black", faces=("north", "down")),
                b("FrontT", (2, 13, 1.5), (12, 15, 1.6), "up-door", faces=N_),
                b("Picker", (5, 4, 4), (9, 7, 7.5), "dk-steel", faces=("north", "east", "west", "up", "down")),
                b("PickerEye", (6.5, 5, 3.9), (7.5, 6, 4), "rk-led-dead", faces=N_),
                b("Shard2", (9.5, 10, 1.2), (11, 12, 1.3), "glass-shard", faces=N_, rot=(0, 0, 35)),
                b("Shard3", (3, 9.5, 1.2), (4.5, 12, 1.3), "glass-shard", faces=N_, rot=(0, 0, -20)),
                b("LcdBezel", (12.5, 8, 1.1), (14.5, 10.5, 1.5), "rk-black", faces=("north", "east", "west", "up", "down")),
                uvb("Lcd", (12.75, 8.3, 1.0), (14.25, 10.2, 1.1), "lcd-dead", (0, 0, 16, 16)),
                uvb("Plate", (12.5, 11, 1.4), (14.5, 12.5, 1.5), "pl-tape", (0, 0, 16, 16))]
    return els


def wreck_elements(state):
    if state == "toppled":
        # A rack fallen on its back: the lower half of a closed rack turned so its front faces the ceiling
        src = rack_elements("lower", "off") + [e for e in rack_elements("upper", "off") if e["name"] in ("Cap", "Brush")]
        out = []
        for e in src:
            if e.get("rotationY") or e.get("rotationX") or e.get("rotationZ"):
                continue
            e = dict(e)
            dy = -1.0 if e["name"] in ("Cap", "Brush") else 0.0
            (x1, y1, z1), (x2, y2, z2) = e["from"], e["to"]
            # Laid on its back (a quarter turn about x, done on the coordinates): the front up, the top to the south
            e["from"], e["to"] = [x1, 16 - z2, y1 + dy], [x2, 16 - z1, y2 + dy]
            remap = {"north": "up", "south": "down", "up": "south", "down": "north", "east": "east", "west": "west"}
            e["faces"] = {remap[k]: v for k, v in e["faces"].items()}
            if e["to"][2] > 16:
                continue
            out.append(e)
        # Its bottom end (the plinth's side), now facing north
        out.append(b("EndN", (0.75, 0.5, 0), (15.25, 15.25, 1.25), {"front": "rk-black", "top": "rk-paint", "side": "rk-paint"}, faces=("north", "up", "east", "west")))
        # One unit slid out onto its front
        out.append(uvb("Slid", (3, 15.9, -0.5), (13, 17.9, 6), "rk-srv", (0, 4, 10, 6), faces=("north", "east", "west", "up"), rest="rk-paint"))
        out[-1]["rotationOrigin"] = [8, 16, 3]
        out[-1]["rotationY"] = 18
        return out
    part = "lower" if state == "tornlower" else "upper"
    els = [e for e in rack_elements(part, "gutted") if not e["name"].startswith(("Door", "Pulled", "RailsOut", "Last"))]
    rng = random.Random("torn-" + part)
    for i in range(3 if part == "lower" else 2):
        y = rng.uniform(3.5, 12)
        u = rng.choice(((0, 4, 10, 6), (0, 0, 10, 1), (0, 8, 10, 10)))
        h = u[3] - u[1]
        els.append(uvb(f"Hang{i}", (3, y, -2.5), (13, y + h, 10), "rk-srv", u, faces=("north", "east", "west", "up", "down"), rest="rk-paint"))
        els[-1]["rotationOrigin"] = [8, y, 3]
        els[-1]["rotationZ"] = rng.choice((-14, -8, 9, 13))
    if part == "lower":
        els.append(b("DoorDown", (0.5, 0, -6), (15, 0.75, 0.5), {"top": "rk-mesh", "side": "rk-paint", "bottom": "rk-paint"},
                     faces=("up", "north", "east", "west"), rot=(0, 7, 0)))
    return els


# ======================================================================== Block types

def blocktypes():
    # The wrecks (the toppled one now a whole cabinet's height)
    shapes = sided("l120-wreck", {s: shape(f"l120-wreck-{s}", wreck_elements(s)) for s in ("toppled", "tornlower", "tornupper")})
    json_block("l120-wreck", [{"code": "state", "states": ["toppled", "tornlower", "tornupper"]}] + SIDED, shapes,
               "Level 120: a rack ripped apart: toppled onto its back, or torn open (two high, lower and upper) with its units hanging out. "
               "Salvage: copper wire, brackets, circuit boards",
               {"collisionbox": cuboid(FULL), "selectionbox": cuboid(FULL)},
               extra={"dropsByType": {"*-toppled-*": drops(("scrapwire", 0.7, 0.5), ("metalbracket", 0.6, 0.4), ("l3999-circuitboard", 0.15, 0)),
                                      "*": drops(("scrapwire", 0.5, 0.4), ("l3999-circuitboard", 0.25, 0), ("metalbracket", 0.3, 0.3))}},
               inventory="l120-wreck-toppled-north")

    shapes = {}
    for part in ("lower", "upper"):
        for state in ("whole", "open"):
            base = shape(f"l120-ups-{part}-{state}", ups_elements(part, state))
            for s in SIDES:
                shapes[f"l120-ups-{part}-{state}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    json_block("l120-ups", [{"code": "part", "states": ["lower", "upper"]}, {"code": "state", "states": ["whole", "open"]}] + SIDED, shapes,
               "Level 120: a UPS cabinet, two high, its front to the side: whole (a louvred door, a dead display and keypad, its breakers "
               "behind a window, UPS 2, DANGER 480 V) or torn open (the battery trays and boards showing, the door down). Salvage: wire, brackets",
               {"collisionbox": cuboid(FULL), "selectionbox": cuboid(FULL)},
               extra={"drops": drops(("scrapwire", 0.5, 0.4), ("metalbracket", 0.5, 0.4))}, inventory="l120-ups-lower-whole-north")

    shapes = sided("l120-battery", {p: shape(f"l120-battery-{p}", battery_elements(p)) for p in ("lower", "upper")})
    json_block("l120-battery", [{"code": "part", "states": ["lower", "upper"]}] + SIDED, shapes,
               "Level 120: a battery cabinet, two high: sealed batteries on shelves behind a door of bars, linked in strings, BATTERY - ACID. "
               "Salvage: brackets", {"collisionbox": cuboid(FULL), "selectionbox": cuboid(FULL)},
               extra={"drops": drops(("metalbracket", 0.5, 0.4))}, inventory="l120-battery-lower-north")

    shapes = sided("l120-crac", {p: shape(f"l120-crac-{p}", crac_elements(p)) for p in ("lower", "loweropen", "upper", "duct")})
    duct = (0.18, 0, 0.25, 0.82, 1, 0.82)
    json_block("l120-crac", [{"code": "part", "states": ["lower", "loweropen", "upper", "duct"]}] + SIDED, shapes,
               "Level 120: a cooling unit (CRAC 3), two high: louvres and latched panels below, its control panel above, its duct up into "
               "the ceiling; now and then its front panel off, the fans and coil showing. Salvage: brackets, wire",
               {"collisionboxByType": {"*-duct-*": cuboid(duct), "*": cuboid(FULL)}, "selectionboxByType": {"*-duct-*": cuboid(duct), "*": cuboid(FULL)}},
               extra={"drops": drops(("metalbracket", 0.5, 0.4), ("scrapwire", 0.3, 0.3))}, inventory="l120-crac-lower-north")

    shapes = sided("l120-terminal", {s: shape(f"l120-terminal-{s}", terminal_elements(s)) for s in ("dead", "smashed", "boot")})
    json_block("l120-terminal", [{"code": "state", "states": ["dead", "smashed", "boot"]}] + SIDED, shapes,
               "Level 120: an operator's desk with a CRT terminal, its keyboard and mouse, its screen to the side: dead, smashed, or whole "
               "(a green BOOT prompt, a little light; right-click to boot it). Salvage: glass, wire, a circuit board",
               {"collisionbox": cuboid(FULL), "selectionbox": cuboid(FULL)},
               extra={"lightHsvByType": {"*-boot-*": [22, 6, 5]},
                      "behaviorsByType": {"*-boot-*": [{"name": "BackroomsL120Boot"}]},
                      "resistanceByType": {"*-boot-*": 40, "*": 3},
                      "dropsByType": {"*-boot-*": [], "*": drops(("glassshard", 0.6, 0.4), ("scrapwire", 0.3, 0.3), ("l3999-circuitboard", 0.25, 0))}},
               inventory="l120-terminal-boot-north")

    shapes = sided("l120-console", {s: shape(f"l120-console-{s}", console_elements(s)) for s in ("dead", "glitch")})
    json_block("l120-console", [{"code": "state", "states": ["dead", "glitch"]}] + SIDED, shapes,
               "Level 120: an operator's desk with two flat monitors on an arm clamped to its back: dead, or one still showing a corrupted "
               "frame of a corridor (a faint light). Salvage: glass, wire",
               {"collisionbox": cuboid(FULL), "selectionbox": cuboid(FULL)},
               extra={"lightHsvByType": {"*-glitch-*": [24, 3, 1]},
                      "drops": drops(("glassshard", 0.5, 0.4), ("scrapwire", 0.3, 0.3))}, inventory="l120-console-dead-north")

    tray = shape("l120-tray", tray_elements())
    # Over a bank, now and then a waterfall of cables drops from the ladder rack into the cabinet's top through its brush
    drop = shape("l120-tray-drop", tray_elements() + [
        b("DropA", (6.6, 0, 7.4), (8.0, 12, 8.8), "cb-blue", faces=("north", "south", "east", "west")),
        b("DropB", (8.2, 0, 7.6), (9.2, 12, 8.6), "cb-grey", faces=("north", "south", "east", "west")),
        b("DropTie", (6.4, 6, 7.2), (9.4, 6.5, 9.0), "rk-black", faces=("north", "south", "east", "west", "up", "down")),
        b("Bend", (6.6, 12, 7.0), (9.2, 12.6, 9.0), "cb-blue", faces=("north", "south", "east", "west", "up"))])
    tb = (0, 0.7, 0.04, 1, 1, 0.8)
    kinds = {"*-we": {"base": tray}, "*-ns": {"base": tray, "rotateY": 90}, "*-wedrop": {"base": drop}, "*-nsdrop": {"base": drop, "rotateY": 90}}
    json_block("l120-tray", [{"code": "kind", "states": ["we", "ns", "wedrop", "nsdrop"]}], kinds,
               "Level 120: an overhead ladder rack on trapeze hangers, cable looms tied along it, the yellow fibre raceway beside it; along x "
               "(we) or z (ns); over a bank now and then a drop of cables into the rack below",
               {"collisionboxByType": {"*-we*": cuboid(tb), "*-ns*": cuboid(tb, 90)},
                "selectionboxByType": {"*-we*": cuboid(tb), "*-ns*": cuboid(tb, 90)}},
               extra={"drops": drops(("scrapwire", 0.5, 0.4))}, inventory="l120-tray-we")

    one = (0.1, 0, 0.1, 0.9, 1, 0.9)
    json_block("l120-kvm", SIDED, {f"l120-kvm-{s}": {"base": shape("l120-kvm", kvm_elements()), "rotateY": ROTATE[s]} for s in SIDES},
               "Level 120: a KVM cart: a steel trolley on casters with a push handle, a monitor on its post, a keyboard, a box and a drive "
               "below, a cable trailing. Salvage: glass, wire",
               {"collisionbox": cuboid(one), "selectionbox": cuboid(one)},
               extra={"drops": drops(("glassshard", 0.4, 0.3), ("scrapwire", 0.3, 0.3))}, inventory="l120-kvm-north")

    shapes = sided("l120-firesup", {p: shape(f"l120-firesup-{p}", firesup_elements(p)) for p in ("lower", "upper", "pipe")})
    pipe = (0.4, 0, 0.7, 0.6, 1, 0.9)
    json_block("l120-firesup", [{"code": "part", "states": ["lower", "upper", "pipe"]}] + SIDED, shapes,
               "Level 120: the fire suppression bank against a wall, two high: three red agent cylinders strapped to their uprights, the "
               "valve heads, hoses to the manifold, and the discharge pipe up into the ceiling. Salvage: brackets",
               {"collisionboxByType": {"*-pipe-*": cuboid(pipe), "*": cuboid((0.05, 0, 0.45, 0.95, 1, 1))},
                "selectionboxByType": {"*-pipe-*": cuboid(pipe), "*": cuboid((0.05, 0, 0.45, 0.95, 1, 1))}},
               extra={"drops": drops(("metalbracket", 0.4, 0.3))}, inventory="l120-firesup-lower-north")

    shapes = sided("l120-tapelib", {p: shape(f"l120-tapelib-{p}", tapelib_elements(p)) for p in ("lower", "upper")})
    json_block("l120-tapelib", [{"code": "part", "states": ["lower", "upper"]}] + SIDED, shapes,
               "Level 120: a tape library, two high: its window smashed, the tapes in their slots behind, the robot's gantry and picker; "
               "TAPE LIB 1. Salvage: wire, brackets",
               {"collisionbox": cuboid(FULL), "selectionbox": cuboid(FULL)},
               extra={"drops": drops(("scrapwire", 0.4, 0.3), ("metalbracket", 0.4, 0.3))}, inventory="l120-tapelib-lower-north")


def main():
    textures()
    floor_textures()
    wall_textures()
    ceiling_textures()
    cardboard_texture()
    more_textures()
    blocktypes()
    blocktypes_more()
    duct_blocktype()
    voiddoor_blocktype()
    lifter_blocktype()


# ======================================================================== The walls, round 4

PAPER4 = (188, 168, 106)


def wall_textures():
    """The dirty yellow wallpaper (matlib paper: fibre, butt seams every half block, a faint stripe and diamond print) and
    the rotting boards behind it (matlib planks, upright, wet and dark), the tears' paper edges curled pale over a shadow."""
    def paper(seed):
        img = M.paper(seed, base=PAPER4, seams=16, seam=0.6, strip=2.5)
        for y in range(32):
            for x in range(32):
                if (x % 8 == 4) and (y % 8 in (2, 6)) or (x % 8 in (3, 5)) and (y % 8 == 4):
                    M.touch(img, x, y, -0.08)
                if x % 16 in (7, 9):
                    M.touch(img, x, y, -0.035)
        M.grime(img, 0.08, seed + 1, color=(120, 100, 60), cells=(8, 4, 2))
        return img

    base = paper(8100)
    save(base, "wall-base")
    stained = paper(8102)
    M.drips(stained, 4, 8103, color=(122, 92, 52), length=(14, 30), strength=0.4, start=0, width=2)
    M.stain(stained, 8104, radius=7, color=(130, 100, 58), strength=0.3, at=(20, 3))
    save(stained, "wall-stained")
    boards = M.wood_planks(8105, base=(66, 48, 34), planks=4, direction="v", contrast=0.8, per_plank=8, gap=(22, 16, 12))
    M.grime(boards, 0.3, 8106, color=(30, 26, 20))
    M.rust(boards, 0.15, 8107, color=(52, 56, 34), dark=(30, 32, 22), pits=False)  # (mould)

    def tear(name, seed, inside):
        img = paper(seed)
        rng = random.Random(seed)
        noise = [[rng.uniform(-1, 1) for _ in range(32)] for _ in range(32)]
        mask = [[inside(x, y, (noise[y][x] + noise[y][(x + 1) % 32] + noise[(y + 1) % 32][x]) / 3) for x in range(32)] for y in range(32)]
        bp, ip = boards.load(), img.load()
        for y in range(32):
            for x in range(32):
                if mask[y][x]:
                    ip[x, y] = bp[x, y]
                    # (the paper's edge above throws a shadow onto the boards)
                    if y > 0 and not mask[y - 1][x]:
                        M.touch(img, x, y, -0.3)
                elif any(0 <= x + dx < 32 and 0 <= y + dy < 32 and mask[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    ip[x, y] = M.rgba(M.lift(PAPER4, 22))
        save(img, name)

    tear("wall-rot", 8110, lambda x, y, n: abs(x - 16 - 3 * math.sin(y * 0.4)) + n * 2.5 < 8 + 2 * math.sin(y * 0.9))
    tear("wall-rot2", 8111, lambda x, y, n: math.hypot((x - 21) / 10.5, (y - 21) / 9.0) + n * 0.22 < 1)
    tear("wall-rot3", 8112, lambda x, y, n: y < 11 + 3.5 * math.sin(x * 0.45 + 1.3) + 2.5 * math.sin(x * 1.3) + n * 2.2)
    soot = M.paper(8113, base=(42, 38, 30), seams=16, seam=0.5, strip=2)
    M.grime(soot, 0.2, 8114, color=(16, 14, 12))
    save(soot, "wall-soot")
    # The skirting: the paper above a dark board along the foot (its top lit, a shadow under the paper's edge), scuffed;
    # stained (a tide line above it), rotting (the board black and soft, the paper torn back over it)
    for name, seed, kind in (("wall-skirt", 8120, 0), ("wall-skirtstain", 8122, 1), ("wall-skirtrot", 8124, 2)):
        img = paper(seed)
        if kind == 1:
            M.tideline(img, 18, seed + 1, color=(126, 96, 56), amount=0.35)
        board = M.wood_planks(seed + 2, base=(70, 50, 34) if kind < 2 else (44, 32, 24), planks=[26, 6], direction="h", contrast=0.7)
        M.grime(board, 0.2 if kind < 2 else 0.4, seed + 3, color=(30, 26, 20))
        M.scratches(board, 3, seed + 4, light=0.15)
        bp, ip = board.load(), img.load()
        top = 26 if kind < 2 else 24
        for y in range(top, 32):
            for x in range(32):
                ip[x, y] = bp[x, y]
        for x in range(32):
            M.touch(img, x, top, 0.25)
            M.touch(img, x, top - 1, -0.25)
        if kind == 2:
            for x in range(32):
                for y in range(top - 6 - int(3 * abs(math.sin(x * 0.5))), top):
                    ip[x, y] = bp[x, (y + 8) % 32]
        save(img, name)


# ======================================================================== Row ends, shelving, the mop, the broken window (round 4)

LETTERS = "ABCDEFGH"


def cutout(img):
    p = img.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b_, a = p[x, y]
            p[x, y] = (r, g, b_, 255 if a >= 128 else 0)
    return img


def more_textures():
    for c in LETTERS:
        def draw(img, d, k, c=c):
            d.rectangle([0, 0, 32 * k, 32 * k], fill=(226, 224, 214))
            d.rectangle([k, k, 31 * k - 1, 31 * k - 1], outline=(24, 24, 24), width=k)
            text_center(d, (0, 2 * k, 32 * k, 10 * k), "ROW", 7 * k, (24, 24, 24))
            text_center(d, (0, 9 * k, 32 * k, 30 * k), c, 20 * k, (24, 24, 24))
        save(M.grime(hires(32, 32, draw), 0.12, 8200 + ord(c)), f"re-plate-{c.lower()}")
    # The broken pane: dirty glass round a jagged hole (cut out), cracks running from it; lower and upper halves
    for part, cy in (("lower", 2), ("upper", 30)):
        rng = random.Random("pane-" + part)
        img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        p = img.load()
        for y in range(32):
            for x in range(32):
                a = math.atan2(y - cy, x - 16)
                r = math.hypot(x - 16, y - cy)
                edge = 13 + 3.5 * math.sin(a * 7 + 1) + 2.0 * math.sin(a * 13) + rng.uniform(-1, 1)
                if r > edge:
                    v = 168 + rng.uniform(-6, 6) + (14 if (x + y) % 13 == 0 else 0)
                    p[x, y] = (int(v * 0.9), int(v), int(v * 1.04), 255)
        for k in range(6):
            a = rng.uniform(0, 2 * math.pi)
            for r in range(10, 30):
                x, y = int(16 + math.cos(a) * r), int(cy + math.sin(a) * r)
                if 0 <= x < 32 and 0 <= y < 32 and p[x, y][3]:
                    p[x, y] = (230, 238, 240, 255)
        M.grime(img, 0.2, 8300, color=(90, 86, 70))
        save(cutout(img), "win-pane-" + part)
    save(M.grime(M.painted_metal(8301, base=(214, 210, 200), panel=False, chips=4, under=(130, 120, 104)), 0.12, 8302), "win-frame")
    save(M.noise_hv((208, 176, 40), 4, 8303, mottle=6), "mop-yellow")


def rowend_elements(part, letter=None):
    """The end of a bank: a panel the bank's full depth, inset in a frame like a rack's side, a kick plate below, the
    top rail and cap above; the upper carries the row's plate, proud on its stand-offs."""
    lower = part == "lower"
    els = [b("Body", (0.5, 0, 0.75), (15.5, 16 if lower else 15, 15.25), {"front": "rk-side", "side": "rk-paint", "back": "rk-paint", "top": "rk-top"},
             faces=("east", "west", "south", "up") if not lower else ("east", "west", "south")),
           b("FrameL", (0.5, 0, 0.25), (2, 16 if lower else 15, 0.75), "rk-paint", faces=("north", "east", "west")),
           b("FrameR", (14, 0, 0.25), (15.5, 16 if lower else 15, 0.75), "rk-paint", faces=("north", "east", "west")),
           b("Panel", (2, 0, 0.5), (14, 16 if lower else 15, 0.75), "rk-side", faces=N_)]
    if lower:
        els += [b("Kick", (0.5, 0, 0.0), (15.5, 1.5, 0.75), "rk-black", faces=("north", "up", "east", "west")),
                b("Grille", (4, 3, 0.35), (12, 6, 0.5), "rk-mesh", faces=N_)]
    else:
        els += [b("Cap", (0, 15, 0.25), (16, 16, 15.75), {"top": "rk-top", "side": "rk-paint"}, faces=ALL),
                b("RailT", (2, 13, 0.25), (14, 15, 0.75), "rk-paint", faces=("north", "down")),
                b("Stand0", (5.5, 9.5, -0.2), (6, 10, 0.5), "rk-chrome", faces=("north", "east", "west", "up", "down")),
                b("Stand1", (10, 3.5, -0.2), (10.5, 4, 0.5), "rk-chrome", faces=("north", "east", "west", "up", "down")),
                uvb("Plate", (4, 2.5, -0.45), (12, 11, -0.2), f"re-plate-{letter.lower()}", (0, 0, 16, 16), faces=("north", "east", "west", "up", "down"),
                    rest="rk-paint"),
                b("Lamp", (7, 11.75, -0.25), (9, 12.5, 0.25), "rk-led-dead", faces=("north", "up", "down"))]
    return els


def shelf_elements(part):
    """Boltless shelving: angle uprights, beams, chipboard decks; drive boxes, caddies and a binder on them."""
    rng = random.Random("shelf4-" + part)
    lower = part == "lower"
    els = []
    for i, (x, z) in enumerate(((0.5, 1), (14.5, 1), (0.5, 14), (14.5, 14))):
        els.append(b(f"Up{i}", (x, 0, z), (x + 1, 16, z + 1), "dk-steel", faces=("north", "east", "south", "west")))
        if lower:
            els.append(b(f"Foot{i}", (x - 0.15, 0, z - 0.15), (x + 1.15, 0.4, z + 1.15), "rk-black", faces=("north", "east", "south", "west", "up")))
    for j, y in enumerate((1, 8.5) if lower else (0.5, 8, 15)):
        els += [b(f"BeamF{j}", (0.5, y, 1), (15.5, y + 1, 1.6), "dk-steel", faces=("north", "up", "down")),
                b(f"BeamB{j}", (0.5, y, 14.4), (15.5, y + 1, 15), "dk-steel", faces=("south", "up", "down")),
                b(f"Deck{j}", (1.5, y + 0.5, 1.6), (14.5, y + 0.9, 14.4), "dk-top", faces=("up", "down"))]
        if y >= 14:
            continue
        x = 1.6
        while x < 13.5:
            w = rng.uniform(2.5, 4.5)
            r = rng.random()
            if r < 0.55:
                h = rng.uniform(3, 5.5)
                z0 = rng.uniform(2, 3.5)
                els.append(b(f"Box{j}{int(x)}", (x, y + 0.9, z0), (min(14.4, x + w), y + 0.9 + h, 13.5), "box-cardboard",
                             faces=("north", "east", "west", "up")))
                els.append(b(f"Tag{j}{int(x)}", (x + 0.5, y + 1.6, z0 - 0.05), (x + 2, y + 2.4, z0), "bk-white", faces=N_))
            elif r < 0.8:
                for k in range(3):
                    xx = x + k * 0.9
                    if xx + 0.8 > 14.4:
                        break
                    els.append(uvb(f"Cad{j}{int(x)}{k}", (xx, y + 0.9, 3), (xx + 0.8, y + 4.4, 10), "rk-srv", (10, 0, 10.4, 3.5),
                                   faces=("north", "up", "east", "west"), rest="rk-paint"))
            elif r < 0.9:
                els.append(b(f"Binder{j}{int(x)}", (x, y + 0.9, 3), (x + 1.2, y + 5.4, 10), "binder", faces=("north", "up", "east", "west")))
                w = 1.4
            x += w + 0.4
    return els


def mop_elements():
    """A yellow mop bucket on casters, its wringer on the rim, the mop standing in it, the handle leant on the rim."""
    els = [b("BucketLo", (4.5, 1, 4.5), (11.5, 3, 11.5), "mop-yellow", faces=("north", "east", "south", "west", "down")),
           b("BucketHi", (4, 3, 4), (12, 6.5, 12), "mop-yellow", faces=("north", "east", "south", "west")),
           b("Rim", (3.75, 6.5, 3.75), (12.25, 7, 12.25), "mop-yellow", faces=("north", "east", "south", "west", "up", "down")),
           b("Water", (4.3, 5.8, 4.3), (11.7, 5.9, 11.7), "cb-black", faces=("up",)),
           b("Wringer", (4.5, 6.5, 4.0), (11.5, 9.5, 7.0), "mop-yellow", faces=("north", "east", "south", "west", "up")),
           b("Lever", (10.8, 9, 5.0), (11.4, 14, 5.6), "rk-chrome", faces=("north", "east", "south", "west", "up"), rot=(0, 0, -20), origin=(11, 9, 5.3)),
           b("Head", (6, 4.5, 7.5), (10.5, 7.5, 11.5), "mophead", faces=("north", "east", "south", "west", "up")),
           b("Handle", (7.7, 5, 8.8), (8.5, 24, 9.6), "wood-handle", faces=("north", "east", "south", "west", "up"), rot=(10, 0, -8), origin=(8, 5, 9))]
    for i, (x, z) in enumerate(((4.5, 4.5), (10.5, 4.5), (4.5, 10.5), (10.5, 10.5))):
        els.append(b(f"Caster{i}", (x, 0, z), (x + 1, 1, z + 1), "rk-black", faces=("north", "east", "south", "west")))
    return els


def window_elements(part):
    """A broken window in a wall (the room to the north): a painted steel frame with its stop, a sill below with a drip
    edge, the pane still in the frame round a jagged hole, glass on the sill."""
    lower = part == "lower"
    y0, y1 = (2, 16) if lower else (0, 13.5)
    els = [b("PostL", (0, 0, 5.5), (2, 16, 10.5), "win-frame", faces=("north", "south", "east", "west")),
           b("PostR", (14, 0, 5.5), (16, 16, 10.5), "win-frame", faces=("north", "south", "east", "west")),
           b("StopL", (2, y0, 7.4), (2.75, y1, 7.8), "win-frame", faces=("north", "east")),
           b("StopR", (13.25, y0, 7.4), (14, y1, 7.8), "win-frame", faces=("north", "west")),
           b("Pane", (2, y0, 7.9), (14, y1, 8.0), "win-pane-" + part, faces=("north", "south"), uv=(1, 0, 13, 14) if lower else (1, 2.5, 13, 16))]
    if lower:
        els += [b("Sill", (1, 0, 4.5), (15, 2, 11.5), "win-frame", faces=("north", "south", "up", "east", "west")),
                b("Drip", (1, 1.25, 4.0), (15, 2, 4.5), "win-frame", faces=("north", "down", "east", "west")),
                b("Glass0", (4, 2, 5), (5.5, 2.1, 6.2), "glass-shard", faces=("up",), rot=(0, 30, 0)),
                b("Glass1", (9, 2, 9.5), (10, 2.1, 10.4), "glass-shard", faces=("up",), rot=(0, -20, 0))]
    else:
        els += [b("Head", (2, 13.5, 5.5), (14, 16, 10.5), "win-frame", faces=("north", "south", "down"))]
    return els


def blocktypes_more():
    shapes = {}
    for s in SIDES:
        shapes[f"l120-rowend-lower-{s}"] = {"base": shape("l120-rowend-lower", rowend_elements("lower")), "rotateY": ROTATE[s]}
        for c in LETTERS:
            shapes[f"l120-rowend-{c.lower()}-{s}"] = {"base": shape(f"l120-rowend-upper-{c.lower()}", rowend_elements("upper", c)), "rotateY": ROTATE[s]}
    json_block("l120-rowend", [{"code": "part", "states": ["lower"] + [c.lower() for c in LETTERS]}] + SIDED, shapes,
               "Level 120: the end panel of a bank of racks, two high (lower; the upper with its ROW plate, a-h, to the side). Salvage: brackets",
               {"collisionbox": cuboid(FULL), "selectionbox": cuboid(FULL)},
               extra={"drops": drops(("metalbracket", 0.4, 0.3))}, inventory="l120-rowend-a-north")
    shapes = sided("l120-shelf", {p: shape(f"l120-shelf-{p}", shelf_elements(p)) for p in ("lower", "upper")})
    json_block("l120-shelf", [{"code": "part", "states": ["lower", "upper"]}] + SIDED, shapes,
               "Level 120: steel shelving, two high, boxed drives, caddies and binders on it. Salvage: brackets, wire",
               {"collisionbox": cuboid(FULL), "selectionbox": cuboid(FULL)},
               extra={"drops": drops(("metalbracket", 0.5, 0.4), ("scrapwire", 0.3, 0.3))}, inventory="l120-shelf-lower-north")
    low = (0.25, 0, 0.25, 0.75, 0.5, 0.75)
    json_block("l120-mop", SIDED, {f"l120-mop-{s}": {"base": shape("l120-mop", mop_elements()), "rotateY": ROTATE[s]} for s in SIDES},
               "Level 120: a yellow mop bucket on casters, its wringer and mop, left behind by whoever cleaned here",
               {"collisionbox": cuboid(low), "selectionbox": cuboid((0.25, 0, 0.25, 0.75, 1, 0.75))},
               extra={"resistance": 1}, inventory="l120-mop-north")
    shapes = sided("l120-window", {p: shape(f"l120-window-{p}", window_elements(p)) for p in ("lower", "upper")})
    json_block("l120-window", [{"code": "part", "states": ["lower", "upper"]}] + SIDED, shapes,
               "Level 120: a broken window at the edge of a pocket, black beyond it (two high): walk into it to go back to the terminal that brought you",
               {"collisionbox": None, "selectionbox": cuboid((0, 0, 0.3, 1, 1, 0.7))},
               extra={"resistance": 40}, inventory="l120-window-lower-north")


# ======================================================================== The passages' duct (round 4)

def duct_run(name, x0=0.0, x1=16.0):
    """A galvanised supply duct along x by the north wall, under the ceiling: its body, a flange at the joint, a band of
    foil tape, the hangers from the slab with the strap under it."""
    return [b(name + "Body", (x0, 9, 1.25), (x1, 15.25, 11), "du-galv", faces=("north", "south", "up", "down", "east", "west")),
            b(name + "Flange", (max(x0, 0), 8.6, 0.85), (max(x0, 0) + 0.6, 15.6, 11.4), "du-galv", faces=("south", "down", "east", "west", "up")),
            b(name + "Tape", (max(x0, 0) + 0.6, 8.95, 1.2), (max(x0, 0) + 2.0, 15.3, 11.05), "du-tape", faces=("south", "down", "up"))]


def duct_elements(kind):
    if kind == "we":
        els = duct_run("D")
        els += [b("StrapU", (9, 8.5, 0.75), (9.75, 9, 11.5), "lr-galv", faces=("south", "down", "east", "west")),
                b("RodS", (9.1, 9, 11.5), (9.6, 16, 12), "lr-galv", faces=("south", "east", "west", "north"))]
        return els
    # The hub: the run along x leaves east, the run along z leaves south, a plenum box where they meet with its access door
    els = duct_run("X", 11, 16)
    # (the run along z, by the west wall, leaving south)
    els += [b("ZBody", (1.25, 9, 11), (11, 15.25, 16), "du-galv", faces=("east", "west", "up", "down", "south")),
            b("ZFlange", (0.85, 8.6, 11.5), (11.4, 15.6, 12.1), "du-galv", faces=("east", "down", "north", "south", "up")),
            b("ZTape", (1.2, 8.95, 12.1), (11.05, 15.3, 13.5), "du-tape", faces=("east", "down", "up"))]
    els += [b("Plenum", (0.75, 8.5, 0.75), (11.5, 15.75, 11.5), "du-galv", faces=("south", "east", "down", "north", "west")),
            b("Access", (4, 9.5, 11.5), (9, 14, 11.75), "dk-drawer", faces=("south", "east", "west", "up", "down")),
            b("Latch", (8, 11.5, 11.75), (8.6, 12.5, 12.0), "rk-black", faces=("south", "east", "west")),
            b("Label", (2, 9.2, 11.5), (4, 10.2, 11.6), "rk-label", faces=("south",), uv=(0, 0, 2, 1))]
    return els


def duct_blocktype():
    run = shape("l120-duct-run", duct_elements("we"))
    hub = shape("l120-duct-hub", duct_elements("hub"))
    bx = (0, 0.53, 0.04, 1, 1, 0.72)
    json_block("l120-duct", [{"code": "kind", "states": ["we", "ns", "hub"]}],
               {"*-we": {"base": run}, "*-ns": {"base": run, "rotateY": 90}, "*-hub": {"base": hub}},
               "Level 120: the passages' supply duct under the ceiling, galvanised, flanged and taped, on its hangers: along x (we), "
               "along z (ns), or the plenum box where two meet",
               {"collisionboxByType": {"*-we": cuboid(bx), "*-ns": cuboid(bx, 90), "*-hub": cuboid((0, 0.53, 0, 1, 1, 1))},
                "selectionboxByType": {"*-we": cuboid(bx), "*-ns": cuboid(bx, 90), "*-hub": cuboid((0, 0.53, 0, 1, 1, 1))}},
               extra={"drops": drops(("metalbracket", 0.3, 0.3))}, inventory="l120-duct-we")


# ======================================================================== The ceiling (round 4)

def ceiling_textures():
    """The office ceiling: matlib's mineral-fibre tile in its T-bar grid, aged and dirtier than the released offices';
    one water-stained; one fallen through, black above it, a ragged edge of tile left in the grid."""
    base = (196, 190, 172)
    tile = M.ceiling_tile(8400, base=base, fissures=0.7)
    M.grime(tile, 0.1, 8401, color=(120, 110, 88))
    save(tile, "ceiling-tile")
    stained = M.ceiling_tile(8402, base=base, fissures=0.7, stain_color=(150, 118, 70))
    M.grime(stained, 0.12, 8403, color=(120, 110, 88))
    save(stained, "ceiling-stained")
    broken = tile.copy()
    p = broken.load()
    rng = random.Random(8404)
    for y in range(2, 30):
        left = 3 + int(2.5 * math.sin(y * 0.7)) + rng.randint(0, 1)
        right = 29 - int(2 * math.sin(y * 0.5 + 1)) - rng.randint(0, 1)
        for x in range(left, right):
            p[x, y] = (8, 8, 9, 255)
        if left - 1 >= 0:
            M.touch(broken, left - 1, y, 0.15)
    save(broken, "ceiling-broken")


def cardboard_texture():
    """Corrugated cardboard: fluting in faint vertical lines, brown packing tape across the top and down the middle, a
    white shipping label, scuffs, a darker foot; laid out so a small box face (its top-left corner of the texture) still
    shows a tape edge and the label."""
    img = M.noise_hv((168, 124, 78), 3, 8500, mottle=6)
    for x in range(0, 32, 4):
        for y in range(32):
            M.touch(img, x, y, -0.02)
    for y in range(2, 5):
        for x in range(32):
            px_set(img, x, y, M.lift((196, 150, 92), random.Random(x * 7 + y).uniform(-3, 3)))
        for x in range(32):
            M.touch(img, x, 5, -0.12)
    for y in range(7, 13):
        for x in range(3, 11):
            px_set(img, x, y, (214, 210, 198) if (y, x % 3) != (9, 0) else (90, 88, 84))
    for x in range(4, 10, 2):
        px_set(img, x, 11, (60, 60, 60))
    M.scratches(img, 4, 8501, light=0.1)
    M.grime(img, 0.12, 8502, color=(100, 80, 56), bias="bottom")
    save(img, "box-cardboard")


def voiddoor_elements(part):
    """A White Void's black door standing open flat against the side of its doorway (the way through along x): a matte
    black leaf with two sunk panels, its lever handle and hinges, and the black frame's edge."""
    lower = part == "lower"
    top = 16 if lower else 15
    els = [b("StileA", (0, 0, 0.5), (1.5, top, 2), "vd-black", faces=("north", "south", "east", "west", "up")),
           b("StileB", (14.5, 0, 0.5), (16, top, 2), "vd-black", faces=("north", "south", "east", "west", "up")),
           b("Panel", (1.5, 0, 0.75), (14.5, top, 1.75), "vd-panel", faces=("north", "south")),
           b("Frame", (0, 0, 0), (16, 16, 0.5), "void-black", faces=("south", "east", "west"))]
    if lower:
        els += [b("RailB", (1.5, 0, 0.5), (14.5, 1.5, 2), "vd-black", faces=("north", "south", "up")),
                b("RailM", (1.5, 15, 0.5), (14.5, 16, 2), "vd-black", faces=("north", "south", "down")),
                b("Rose", (12.5, 14.5, 2), (13.5, 15.5, 2.2), "rk-chrome", faces=("south", "east", "west", "up", "down")),
                b("Lever", (10.5, 14.75, 2.2), (13.25, 15.25, 2.7), "rk-chrome", faces=("south", "east", "west", "up", "down")),
                b("Hinge0", (0.25, 3, 2), (1.0, 5, 2.4), "rk-chrome", faces=("south", "east", "west", "up", "down"))]
    else:
        els += [b("RailM", (1.5, 0, 0.5), (14.5, 1, 2), "vd-black", faces=("north", "south", "up")),
                b("RailT", (1.5, 13.5, 0.5), (14.5, 15, 2), "vd-black", faces=("north", "south", "down", "up")),
                b("Hinge1", (0.25, 9, 2), (1.0, 11, 2.4), "rk-chrome", faces=("south", "east", "west", "up", "down"))]
    return els


def voiddoor_blocktype():
    save(M.painted_metal(8600, base=(24, 24, 26), panel=False, chips=1, under=(60, 60, 62)), "vd-black")
    save(M.painted_metal(8601, base=(20, 20, 22), panel=True, chips=0), "vd-panel")
    shapes = {}
    for part in ("lower", "upper"):
        base = shape("l120-voiddoor-" + part, voiddoor_elements(part))
        shapes[f"l120-voiddoor-{part}-we"] = {"base": base}
        shapes[f"l120-voiddoor-{part}-ns"] = {"base": base, "rotateY": 90}
    leaf = (0, 0, 0, 1, 1, 0.125)
    json_block("l120-voiddoor", [{"code": "part", "states": ["lower", "upper"]}, {"code": "way", "states": ["we", "ns"]}], shapes,
               "Level 120: a White Void's black door, standing open against the side of its doorway (two high; the way through along x or z)",
               {"collisionboxByType": {"*-we": cuboid(leaf), "*-ns": cuboid(leaf, 90)}, "selectionboxByType": {"*-we": cuboid(leaf), "*-ns": cuboid(leaf, 90)}},
               extra={"resistance": 40}, inventory="l120-voiddoor-lower-we")


def lifter_elements():
    """A raised-floor panel lifted out and left on the floor beside its hole (its front toward the hole, north), the
    suction lifter still on it: two rubber cups and a handle."""
    r = (0, 18, 0)
    o = (8, 0, 9)
    els = [b("Panel", (4, 0, 5), (12, 1.25, 13), {"top": "floor-dirty", "side": "dk-steel", "bottom": "dk-steel"}, faces=("up", "north", "south", "east", "west"),
             rot=r, origin=o),
           b("CupA", (5, 1.25, 8.2), (7, 1.85, 9.8), "rk-black", faces=("up", "north", "south", "east", "west"), rot=r, origin=o),
           b("CupB", (9, 1.25, 8.2), (11, 1.85, 9.8), "rk-black", faces=("up", "north", "south", "east", "west"), rot=r, origin=o),
           b("PostA", (5.75, 1.85, 8.75), (6.25, 3.3, 9.25), "rk-chrome", faces=("north", "south", "east", "west"), rot=r, origin=o),
           b("PostB", (9.75, 1.85, 8.75), (10.25, 3.3, 9.25), "rk-chrome", faces=("north", "south", "east", "west"), rot=r, origin=o),
           b("Grip", (5.5, 3.3, 8.6), (10.5, 3.9, 9.4), "fibre-y", faces=("up", "north", "south", "east", "west", "down"), rot=r, origin=o)]
    els[0]["faces"]["up"]["uv"] = [0, 0, 8, 8]
    return els


def lifter_blocktype():
    shapes = sided("l120-lifter", {"": shape("l120-lifter", lifter_elements())})
    json_block("l120-lifter", SIDED, shapes,
               "Level 120: a raised-floor panel lifted out and left beside its hole, the suction lifter still on it (walked over)",
               {"collisionbox": None, "selectionbox": cuboid((0.2, 0, 0.2, 0.8, 0.25, 0.85))},
               extra={"resistance": 1, "drops": drops(("metalbracket", 0.2, 0))}, inventory="l120-lifter-north")
