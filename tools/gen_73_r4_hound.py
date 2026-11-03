"""Level 73, "The Redlands": round 4's (2026-11-02) Great Hound, sculpted; called from gen_73.py (run that, under the asset lock).

The lead on round 3: "The Great Hound skeleton is joined thin lines; sculpt it (skull with jaw and teeth, ribcage, spine,
limbs) as a multi-block piece". The skeleton is drawn as bones, each a box laid along its length and turned about one axis
(the spine and tail in the upright plane along the body, the ribs in the upright plane across it, the legs flat on the
ground), with knobs at the joints; the skull built up of its cranium, brow, cheekbones, snout, the jaw dropped open with its
teeth, the sockets and the nose dark. The whole is cut by where along the body each bone lies into the models of eleven
anchor blocks (l73-hound-{k}) on the skeleton's axis one over the ground: anchor k at skeleton-local x = 1 + 4k, z 0, h 1
(WorldLayout.Level73's L73Hound: x from the snout's tip eastward, z across, h over the ground it lies on).

Skeleton-local continuous coordinates (blocks): X along the body (0 the snout's tip), Z across (0.5 its middle), H over the
ground's top (1.0 the ground).
"""
import math
import os

from gen_73_castle import face, fixed, shape


def box(name, frm, to, tex):
    """A box anywhere (far outside its block), each face mapped by its own size (up to the texture's 16), offset by where
    it lies so neighbouring bones do not repeat the same patch."""
    (x1, y1, z1), (x2, y2, z2) = frm, to
    dims = {"north": (x2 - x1, y2 - y1), "south": (x2 - x1, y2 - y1), "east": (z2 - z1, y2 - y1), "west": (z2 - z1, y2 - y1),
            "up": (x2 - x1, z2 - z1), "down": (x2 - x1, z2 - z1)}
    off = int(abs(x1 * 7 + y1 * 3 + z1 * 5)) % 8
    fs = {}
    for k, (w, h) in dims.items():
        w, h = min(16, abs(w)), min(16, abs(h))
        u0 = min(off, 16 - w)
        v0 = min((off * 3) % 8, 16 - h)
        fs[k] = face(tex, [round(u0, 3), round(v0, 3), round(u0 + w, 3), round(v0 + h, 3)])
    return {"name": name, "from": [round(v, 3) for v in frm], "to": [round(v, 3) for v in to], "faces": fs}

T = "backrooms:block/73/"
TEX = {"bone": T + "bone", "old": T + "bone-2", "dark": T + "r4-dark"}
ANCHORS = [1 + 4 * k for k in range(10)]
LANG = [("block-l73-hound-*", "Bones of the Great Hound")]

GROUND = 1.0
MID = 0.5


def spine_h(x):
    """The spine's height along the body: arched over the ribs, low at the shoulders and the hips."""
    if x <= 10:
        return 5.4
    if x >= 29:
        return 5.0
    return 5.0 + 2.5 * math.sin(math.pi * (x - 10) / 19) ** 0.8 + 0.4 * (29 - x) / 19


class Bones:
    def __init__(self):
        self.parts = []  # (x_mid, element) in skeleton blocks; the element in skeleton px (converted per anchor)

    def add(self, el, xmid):
        self.parts.append((xmid, el))

    def cube(self, name, a, b, tex="#bone"):
        """An axis-aligned box from a to b, (X, H, Z) in blocks."""
        (x0, h0, z0), (x1, h1, z1) = a, b
        self.add(box(name, [x0 * 16, h0 * 16, z0 * 16], [x1 * 16, h1 * 16, z1 * 16], tex), (x0 + x1) / 2)

    def bone(self, name, p, q, w=0.2, t=0.2, tex="#bone", knobs=0.0):
        """A bone from p to q (X, H, Z) lying in one of the three planes, w x t thick; knobs: a knob of that size at each end."""
        (x0, h0, z0), (x1, h1, z1) = p, q
        dx, dh, dz = x1 - x0, h1 - h0, z1 - z0
        cx, ch, cz = (x0 + x1) / 2, (h0 + h1) / 2, (z0 + z1) / 2
        o = [cx * 16, ch * 16, cz * 16]
        if abs(dz) < 1e-6:  # in the upright plane along the body: a box along x turned about z
            L = math.hypot(dx, dh)
            el = box(name, [(cx - L / 2) * 16, (ch - t / 2) * 16, (cz - w / 2) * 16], [(cx + L / 2) * 16, (ch + t / 2) * 16, (cz + w / 2) * 16], tex)
            el["rotationOrigin"] = o
            el["rotationZ"] = round(math.degrees(math.atan2(dh, dx)), 3)
        elif abs(dx) < 1e-6:  # in the upright plane across the body: a box along z turned about x
            L = math.hypot(dz, dh)
            el = box(name, [(cx - w / 2) * 16, (ch - t / 2) * 16, (cz - L / 2) * 16], [(cx + w / 2) * 16, (ch + t / 2) * 16, (cz + L / 2) * 16], tex)
            el["rotationOrigin"] = o
            el["rotationX"] = round(math.degrees(math.atan2(-dh, dz)), 3)
        else:  # flat on the ground: a box along x turned about y (dh ignored)
            L = math.hypot(dx, dz)
            el = box(name, [(cx - L / 2) * 16, (ch - t / 2) * 16, (cz - w / 2) * 16], [(cx + L / 2) * 16, (ch + t / 2) * 16, (cz + w / 2) * 16], tex)
            el["rotationOrigin"] = o
            el["rotationY"] = round(math.degrees(math.atan2(-dz, dx)), 3)
        self.add(el, cx)
        if knobs:
            for i, (x, h, z) in enumerate((p, q)):
                k = knobs / 2
                self.cube(f"{name}K{i}", (x - k, h - k, z - k), (x + k, h + k, z + k), tex)


def build():
    b = Bones()
    # ---- The skull (west end, x 0-7.6), lying with its jaw on the ground, a little open ----
    b.cube("Cranium", (3.4, 1.9, MID - 2.0), (7.0, 4.3, MID + 2.0))
    b.cube("CraniumTop", (3.8, 4.3, MID - 1.5), (6.6, 4.7, MID + 1.5))
    b.cube("Crest", (4.2, 4.7, MID - 0.18), (7.4, 5.1, MID + 0.18), "#old")
    b.cube("Occiput", (7.0, 2.4, MID - 1.5), (7.6, 4.0, MID + 1.5), "#old")
    b.cube("Condyles", (7.4, 2.2, MID - 0.6), (7.9, 2.8, MID + 0.6), "#old")
    b.cube("BrowL", (3.0, 3.7, MID - 2.1), (4.4, 4.2, MID - 0.3))
    b.cube("BrowR", (3.0, 3.7, MID + 0.3), (4.4, 4.2, MID + 2.1))
    b.cube("SocketL", (3.15, 2.85, MID - 2.05), (4.25, 3.7, MID - 1.3), "#dark")
    b.cube("SocketR", (3.15, 2.85, MID + 1.3), (4.25, 3.7, MID + 2.05), "#dark")
    b.cube("CheekL", (2.6, 2.1, MID - 2.35), (5.4, 2.6, MID - 1.9))
    b.cube("CheekR", (2.6, 2.1, MID + 1.9), (5.4, 2.6, MID + 2.35))
    b.cube("Snout", (0.9, 2.2, MID - 1.0), (3.4, 3.5, MID + 1.0))
    b.cube("SnoutTip", (0.2, 2.2, MID - 0.75), (0.9, 3.15, MID + 0.75))
    b.cube("SnoutRidge", (0.6, 3.5, MID - 0.45), (3.6, 3.8, MID + 0.45), "#old")
    b.cube("Nose", (0.15, 2.6, MID - 0.45), (0.3, 3.05, MID + 0.45), "#dark")
    b.cube("Palate", (0.4, 2.0, MID - 0.95), (3.6, 2.2, MID + 0.95), "#old")
    # the upper teeth: fangs at the front, a row behind
    for side in (-1, 1):
        z = MID + side * 0.82
        b.cube(f"Fang{side}", (0.55, 1.45, z - 0.13), (0.85, 2.05, z + 0.13))
        for i in range(6):
            x = 1.1 + 0.42 * i
            b.cube(f"Tooth{side}{i}", (x, 1.82, z - 0.1), (x + 0.24, 2.0 + (0.08 if i % 2 else 0), z + 0.1))
    # the lower jaw, dropped: two rami from the hinge under the cheek to the chin on the ground
    for side in (-1, 1):
        z = MID + side * 0.85
        b.bone(f"Jaw{side}", (0.5, GROUND + 0.22, z), (5.2, 2.05, z), w=0.32, t=0.42)
        b.cube(f"JawHinge{side}", (5.0, 1.9, z - 0.25), (5.6, 2.4, z + 0.25), "#old")
        b.cube(f"LowFang{side}", (0.75, GROUND + 0.35, z - 0.12), (1.0, GROUND + 0.95, z + 0.12))
        for i in range(5):
            x = 1.3 + 0.5 * i
            hh = GROUND + 0.3 + (x - 0.5) * (2.05 - GROUND - 0.22) / 4.7
            b.cube(f"LowTooth{side}{i}", (x, hh + 0.12, z - 0.09), (x + 0.22, hh + 0.36, z + 0.09))
    b.cube("Chin", (0.4, GROUND, MID - 0.9), (1.0, GROUND + 0.3, MID + 0.9))
    # ---- The neck: vertebrae rising from the skull to the shoulders ----
    for i in range(5):
        x = 7.9 + 0.55 * i
        h = 2.6 + (spine_h(10.4) - 2.6) * (i + 1) / 6
        b.cube(f"Neck{i}", (x, h - 0.32, MID - 0.36), (x + 0.42, h + 0.32, MID + 0.36))
        b.cube(f"NeckSpur{i}", (x + 0.1, h + 0.32, MID - 0.12), (x + 0.32, h + 0.62, MID + 0.12), "#old")
    # ---- The spine, arched: a centrum, a neural spine leaning back, transverse processes ----
    x = 10.6
    i = 0
    while x < 29.4:
        h = spine_h(x)
        b.cube(f"Vert{i}", (x, h - 0.34, MID - 0.38), (x + 0.5, h + 0.34, MID + 0.38))
        tall = 0.9 if 12 < x < 22 else 0.6
        b.bone(f"Spur{i}", (x + 0.2, h + 0.3, MID), (x + 0.45, h + 0.3 + tall, MID), w=0.16, t=0.22, tex="#old")
        b.cube(f"Proc{i}", (x + 0.1, h - 0.12, MID - 0.75), (x + 0.4, h + 0.08, MID + 0.75), "#old")
        x += 0.72
        i += 1
    # ---- The ribs: nine pairs curving out from the spine and down to the ground; two broken ----
    for n in range(9):
        rx = 12.0 + 1.45 * n
        hs = spine_h(rx) - 0.2
        reach = 2.8 + 1.7 * math.sin(math.pi * (rx - 11) / 14)
        for side in (-1, 1):
            broken = (n == 4 and side < 0) or (n == 7 and side > 0)
            segs = 3 if broken else 6
            pts = []
            for k in range(segs + 1):
                t = k / 6
                a = t * math.pi / 2
                z = MID + side * (0.45 + reach * math.sin(a) ** 0.9)
                h = hs - (hs - GROUND - 0.2) * (1 - math.cos(a))
                pts.append((rx, h, z))
            for k in range(segs):
                b.bone(f"Rib{n}{side}{k}", pts[k], pts[k + 1], w=0.22, t=0.2, tex="#bone" if k % 2 else "#old")
            if broken:
                # the broken-off piece lying on the ground below it
                b.bone(f"RibBit{n}{side}", (rx - 0.6, GROUND + 0.1, MID + side * (reach - 0.4)), (rx + 0.9, GROUND + 0.1, MID + side * (reach + 0.3)),
                       w=0.2, t=0.18, tex="#old")
    # ---- The shoulder blades against the front ribs ----
    for side in (-1, 1):
        z = MID + side * 2.2
        b.bone(f"Scapula{side}", (11.0, 2.4, MID + side * 2.6), (11.0, 4.6, MID + side * 1.2), w=1.1, t=0.18, tex="#old")
    # ---- The pelvis: the wings of the hips either side of the spine, and the bar between ----
    for side in (-1, 1):
        b.bone(f"Ilium{side}", (28.0, 3.0, MID + side * 2.0), (28.0, 5.0, MID + side * 0.7), w=1.6, t=0.22)
        b.cube(f"Socket{side}", (28.6, 2.6, MID + side * 2.0 - 0.3), (29.4, 3.2, MID + side * 2.0 + 0.3), "#old")
        b.bone(f"Ischium{side}", (28.9, 2.6, MID + side * 1.6), (30.6, 3.4, MID + side * 1.6), w=0.4, t=0.35)
    b.cube("Sacrum", (27.4, 4.4, MID - 0.6), (30.2, 5.1, MID + 0.6), "#old")
    # ---- The legs, stretched out flat: forelegs forward, hind legs back; knobbed joints; the paws' toes ----
    g = GROUND + 0.2
    for side in (-1, 1):
        s = side
        sh, el, wr = (11.6, g, MID + s * 3.0), (9.4, g, MID + s * 4.4), (6.9, g, MID + s * 5.2)
        b.bone(f"Humerus{s}", sh, el, w=0.42, t=0.4, knobs=0.62)
        b.bone(f"Radius{s}", el, wr, w=0.32, t=0.3, knobs=0.46)
        hip, knee, ank = (29.2, g, MID + s * 2.4), (31.6, g, MID + s * 3.6), (34.4, g, MID + s * 4.3)
        b.bone(f"Femur{s}", hip, knee, w=0.46, t=0.42, knobs=0.66)
        b.bone(f"Tibia{s}", knee, ank, w=0.34, t=0.32, knobs=0.48)
        for foot, (fx, fz), d in (("F", wr[::2], -1), ("H", ank[::2], 1)):
            for k in range(4):
                spread = (k - 1.5) * 0.32
                end = (fx + d * 1.15, g - 0.05, fz + s * 0.15 + spread)
                b.bone(f"Toe{foot}{s}{k}", (fx + d * 0.1, g, fz + spread * 0.4), end, w=0.13, t=0.14)
                b.cube(f"Claw{foot}{s}{k}", (end[0] - 0.12 + d * 0.12, GROUND, end[2] - 0.07), (end[0] + 0.12 + d * 0.12, GROUND + 0.2, end[2] + 0.07), "#old")
    # ---- The tail, falling to the ground and curling aside ----
    prev = (30.2, 4.6, MID)
    for k in range(12):
        x = 30.9 + 0.7 * k
        h = max(GROUND + 0.18, 4.6 - 0.62 * (k + 1))
        cur = (x, h, MID)
        sz = 0.36 - 0.02 * k
        b.cube(f"Tail{k}", (x - sz, h - sz * 0.8, MID - sz * 0.8 + 0.08 * k), (x + sz, h + sz * 0.8, MID + sz * 0.8 + 0.08 * k), "#bone" if k % 2 else "#old")
        prev = cur
    return b


def anchor_of(xmid):
    return min(range(len(ANCHORS)), key=lambda k: abs(ANCHORS[k] + 0.5 - xmid))


def models():
    """The eleven anchors' shapes: each bone in the anchor nearest its middle, moved into that block's frame."""
    b = build()
    out = [[] for _ in ANCHORS]
    for xmid, el in b.parts:
        k = anchor_of(xmid)
        ax = ANCHORS[k]
        # skeleton px -> anchor px: the anchor block is at (ax, h 1, z 0); skeleton H is measured from the ground's top,
        # which is the anchor block's bottom (h 1 = the first block over the ground)
        def mv(p):
            return [round(p[0] - ax * 16, 3), round(p[1] - GROUND * 16, 3), round(p[2], 3)]
        el = dict(el)
        el["from"], el["to"] = mv(el["from"]), mv(el["to"])
        if "rotationOrigin" in el:
            el["rotationOrigin"] = mv(el["rotationOrigin"])
        out[k].append(el)
    return out


def textures(save):
    return 0


def blocktypes():
    states = [str(k) for k in range(len(ANCHORS))]
    return [("// Level 73: the Great Hound's bones, sculpted (round 4): one block on the skeleton's axis carries the bones about it", fixed({
        "code": "l73-hound", "variantgroups": [{"code": "part", "states": states}],
        "creativeinventory": {"general": ["*-0"], "backrooms": ["*-0"]}, "blockmaterial": "Stone", "drawtype": "json",
        "shapeByType": {f"*-{k}": {"base": f"block/73/hound-{k}"} for k in states},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0,
        "selectionbox": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 1, "z2": 1}, "collisionbox": None, "drops": [],
        "sounds": {"walk": "game:walk/stone*", "place": "game:block/rock-hit-pickaxe", "break": "game:block/rock-hit-pickaxe", "hit": "game:block/rock-hit-pickaxe"}}))]


def shapes(write_json, shape_dir):
    ms = models()
    for k, els in enumerate(ms):
        write_json(os.path.join(shape_dir, f"hound-{k}.json"), None, shape(TEX, els))
    return len(ms)


if __name__ == "__main__":
    for k, els in enumerate(models()):
        print(k, len(els))
