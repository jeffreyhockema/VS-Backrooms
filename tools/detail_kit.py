"""Shared helpers for gen_detail.py: boxes, shapes, block types and names for the detail props.

Every model is built from boxes in block space (0-16 per axis, may reach outside the block). Props are modelled
with their front facing north (toward -Z); wall decorations stick out of the north face of a wall block. Block
variants rotate them to the other three sides.
"""
import json
import os
import sys
import zlib

sys.path.insert(0, os.path.dirname(__file__))
import gen_textures as T  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")

SIDES = ["north", "east", "south", "west"]
ROTATE = {"north": 0, "east": 270, "south": 180, "west": 90}
DIRS = ("north", "east", "south", "west", "up", "down")

STONE = {"walk": "game:walk/stone", "place": "game:block/loosestone", "break": "game:block/rock-break-pickaxe", "hit": "game:block/rock-hit-pickaxe"}
WOOD = {"walk": "game:walk/wood", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"}
METAL = {"walk": "game:walk/stone", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"}
GLASS = {"walk": "game:walk/stone", "place": "game:block/glass", "break": "game:block/glass", "hit": "game:block/glass"}
CLOTH = {"walk": "game:walk/cloth", "place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"}

DEAD_LIGHT_DROPS = [
    {"type": "item", "code": "glassshard", "quantity": {"avg": 1.5, "var": 0.5}},
    {"type": "item", "code": "metalbracket", "quantity": {"avg": 0.12, "var": 0}},
    {"type": "item", "code": "scrapwire", "quantity": {"avg": 0.3, "var": 0}},
]
CEILING_DROPS = [
    {"type": "item", "code": "scrapwire", "quantity": {"avg": 0.12, "var": 0}},
    {"type": "item", "code": "metalbracket", "quantity": {"avg": 0.04, "var": 0}},
    {"type": "item", "code": "rottenwood", "quantity": {"avg": 0.1, "var": 0}},
]

# Texture keys that already exist elsewhere in the mod; any other key is a new texture in block/detail/
EXT = {
    "concretewall": "backrooms:block/level1/concretewall-plain",
    "pillar": "backrooms:block/level1/concretepillar-plain",
    "concretefloor": "backrooms:block/level1/concretefloor-plain",
    "drywall": "backrooms:block/level4/officewall",
    "glazed": "backrooms:block/level3/l3wall-glazed",
    "brick": "backrooms:block/level3/l3wall-brick",
    "cinder": "backrooms:block/level3/l3wall-cinder",
    "hotelpanel": "backrooms:block/level5/hotelwall-panel",
    "wainscot": "backrooms:block/level5/hotelwall-wainscot",
    "frieze": "backrooms:block/level5/hotelwall-frieze",
    "plaster": "backrooms:block/level5/plaster",
    "metal": "backrooms:block/props/metal",
    "metaldark": "backrooms:block/props/metal-dark",
    "rust": "backrooms:block/level2/pipe-rust",
    "lagging": "backrooms:block/level2/pipe-lagging",
    "redpipe": "backrooms:block/level2/pipe-red",
    "valve": "backrooms:block/props/valve",
    "tube": "backrooms:block/props/tube-white",
    "tubewarm": "backrooms:block/props/tube-warm",
    "tubeoff": "backrooms:block/props/tube-off",
    "cardboard": "backrooms:block/supplybox-side",
    "cardboardtop": "backrooms:block/supplybox-top",
    "mahogany": "backrooms:block/level5/mahogany",
    "brass": "backrooms:block/level5/brass",
    "gilt": "backrooms:block/level5/gilt",
    "velvet": "backrooms:block/level5/velvet",
    "linen": "backrooms:block/level5/linen",
    "lampshade": "backrooms:block/level5/lampshade",
    "crystal": "backrooms:block/level5/crystal",
    "felt": "backrooms:block/level5/felt",
    "mahjong": "backrooms:block/level5/mahjong",
    "laminate": "backrooms:block/level4/laminate",
    "crt": "backrooms:block/level4/crt",
    "crtscreen": "backrooms:block/level4/crt-screen",
    "chairfabric": "backrooms:block/level4/chairfabric",
    # (B7) Level 4's furniture materials, shared by gen_shapes' office models and the props here
    "chairplastic": "backrooms:block/level4/chairplastic",
    "lamedge": "backrooms:block/level4/laminate-edge",
    "lamfleck": "backrooms:block/level4/laminate-fleck",
    "alu": "backrooms:block/level4/partitionrail-top",
    "cable": "backrooms:block/level3/cable",
    "insulator": "backrooms:block/level3/insulator",
    "transformer": "backrooms:block/level3/transformer",
    "panel": "backrooms:block/level3/panel",
    "cratewood": "backrooms:block/level1/crate-side",
    # (B6) Level 3's modelled wall fittings share the materials of the wall fixtures and of Level 2's cabinets
    "l3paint": "backrooms:block/level3/panel-paint",
    "l3face": "backrooms:block/level3/panel-face",
    "tray": "backrooms:block/level3/tray",
    "wallrust": "backrooms:block/level2/wallpipe-rust",
    "flange": "backrooms:block/level2/wallpipe-flange",
    "walllag": "backrooms:block/level2/wallpipe-lagging",  # (D4) Level 5's boiler bays: the lagged pipe, round
    "riserrust": "backrooms:block/level3/riser-rust",
    "riserlag": "backrooms:block/level3/riser-lagging",
    "cabdial": "backrooms:block/level2/cabinet-dial",
    "cabneedle": "backrooms:block/level2/cabinet-needle",
    "cabbezel": "backrooms:block/level2/cabinet-bezel",
    "cablabel": "backrooms:block/level2/cabinet-label",
    "warn3": "backrooms:block/level3/warning",
    "fanwell": "backrooms:block/level3/fan-well",
    "fanblade": "backrooms:block/level3/fan-blade",
    "cablampred": "backrooms:block/level2/cabinet-lampred",
    "cablampamber": "backrooms:block/level2/cabinet-lampamber",
}
for _i in range(8):
    EXT[f"roomsign{_i}"] = f"backrooms:block/level3/roomsign-{_i}"

LANG = {}
MANIFEST = {}


def tpath(key):
    return EXT.get(key, f"backrooms:block/detail/{key}")


def seed_of(name):
    return zlib.crc32(name.encode()) & 0xFFFF


# ---------------- Boxes ----------------

def bx(name, frm, to, tex, glow=0, faces=DIRS, full=False, rot=None, origin=None, uv=None):
    """A box. UVs follow its own size so textures keep their scale, unless `full` stretches the whole texture over
    every face (for signs and pictures) or `uv` gives one explicitly. `rot` is (x, y, z) degrees about `origin`."""
    (x1, y1, z1), (x2, y2, z2) = frm, to
    w, h, d = abs(x2 - x1), abs(y2 - y1), abs(z2 - z1)
    sizes = {"north": (w, h), "south": (w, h), "east": (d, h), "west": (d, h), "up": (w, d), "down": (w, d)}
    out = {}
    for f in faces:
        if uv is not None:
            face_uv = list(uv)
        elif full:
            face_uv = [0, 0, 16, 16]
        else:
            a, b = sizes[f]
            face_uv = [0, 0, min(16, max(a, 0.5)), min(16, max(b, 0.5))]
        face = {"texture": "#" + tex, "uv": face_uv}
        if glow:
            face["glow"] = glow
        out[f] = face
    el = {"name": name, "from": [x1, y1, z1], "to": [x2, y2, z2], "faces": out}
    if rot:
        el["rotationOrigin"] = list(origin) if origin else [(x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2]
        if rot[0]:
            el["rotationX"] = rot[0]
        if rot[1]:
            el["rotationY"] = rot[1]
        if rot[2]:
            el["rotationZ"] = rot[2]
    return el


def turn(el, times):
    """Rotates an unrotated box 90 degrees clockwise (seen from above) around the block centre."""
    el = json.loads(json.dumps(el))
    for _ in range(times % 4):
        (x1, y1, z1), (x2, y2, z2) = el["from"], el["to"]
        el["from"], el["to"] = [16 - z2, y1, x1], [16 - z1, y2, x2]
        f = el["faces"]
        el["faces"] = {k: v for k, v in {
            "east": f.get("north"), "south": f.get("east"), "west": f.get("south"), "north": f.get("west"),
            "up": f.get("up"), "down": f.get("down"),
        }.items() if v is not None}
    return el


def shift(els, dx=0, dy=0, dz=0):
    out = []
    for e in els:
        e = json.loads(json.dumps(e))
        e["from"] = [e["from"][0] + dx, e["from"][1] + dy, e["from"][2] + dz]
        e["to"] = [e["to"][0] + dx, e["to"][1] + dy, e["to"][2] + dz]
        if "rotationOrigin" in e:
            o = e["rotationOrigin"]
            e["rotationOrigin"] = [o[0] + dx, o[1] + dy, o[2] + dz]
        out.append(e)
    return out


def clip_x(el, x_lo, x_hi):
    """Cuts an unrotated box down to x_lo..x_hi, leaving its pictures where they were: each face's UVs are cut in the
    same proportion (a north face's U runs from east to west, as it is seen from the north; the others' west to east),
    and an end face left on a cut is dropped. None if nothing of the box is left."""
    assert not any(k in el for k in ("rotationX", "rotationY", "rotationZ")), el["name"]
    el = json.loads(json.dumps(el))
    (x1, _, _), (x2, _, _) = el["from"], el["to"]
    n1, n2 = max(x1, x_lo), min(x2, x_hi)
    if n2 <= n1:
        return None
    for k, f in el["faces"].items():
        if k in ("east", "west"):
            continue
        u1, v1, u2, v2 = f["uv"]

        def u_at(x):
            t = (x2 - x) / (x2 - x1) if k == "north" else (x - x1) / (x2 - x1)
            return round(u1 + t * (u2 - u1), 4)
        f["uv"] = [u_at(n2), v1, u_at(n1), v2] if k == "north" else [u_at(n1), v1, u_at(n2), v2]
    if n1 > x1:
        el["faces"].pop("west", None)
    if n2 < x2:
        el["faces"].pop("east", None)
    el["from"][0], el["to"][0] = n1, n2
    return el


def seam_halves(els):
    """A sign modelled centred on a block (x = 8), split into the two halves that draw it centred on the seam between
    two blocks side by side, for a sign over a two-wide doorway. Returns (left, right). `left` is the half a viewer
    in front of the north face sees on the left: it lies in the block east of the seam, from its west edge (x 0) on.
    `right` lies in the block west of the seam, up to its east edge (x 16). A face a half has on the seam is dropped,
    and the pictures are cut so the two halves read as one; the sign's south face, if it has one, is split to match
    (seen from the south, `right` carries its left half)."""
    left = [e for e in (clip_x(e, 0, 16) for e in shift(els, dx=-8)) if e]
    right = [e for e in (clip_x(e, 0, 16) for e in shift(els, dx=8)) if e]
    return left, right


def cube(tex):
    return bx("Wall", (0, 0, 0), (16, 16, 16), tex)


def cyl(name, cx, cz, r, y1, y2, tex, glow=0, steps=2):
    """A rough vertical cylinder from a cross of boxes."""
    els = [bx(name, (cx - r, y1, cz - r * 0.7), (cx + r, y2, cz + r * 0.7), tex, glow),
           bx(name + "b", (cx - r * 0.7, y1, cz - r), (cx + r * 0.7, y2, cz + r), tex, glow)]
    return els


# ---------------- Files ----------------

def write_json(path, data, comment=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(data, indent="\t")
    if comment:
        text = "// " + comment + "\n" + text
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")


# ---------------- Ground storage ----------------
# Every item can be set down on the floor (shift + right-click on the top of a block), laid out the way vanilla lays
# out its own: Quadrants puts four small things to a block, Messy12 scatters a dozen loose bits, Halves lays two long
# tools side by side, SingleCenter puts one thing in the middle. The game lays a flat item (a texture, no shape) flat
# at a third of a block across; FLAT_SCALE enlarges it to suit the layout.
FLAT_SCALE = {"Quadrants": 1.3, "Messy12": 0.8, "Halves": 1.5, "SingleCenter": 2}


def _cuboid(x1, y1, z1, x2, y2, z2):
    return {"x1": x1, "y1": y1, "z1": z1, "x2": x2, "y2": y2, "z2": z2}


def ground_storable(data, layout="Quadrants", scale=None, ctrl=False, height=None, box=None, select=None, transform=None):
    """Makes an item type ground-storable, in place, and returns it.

    ctrl: placed with ctrl + shift, as vanilla's tools are (for things whose own use is shift + right-click), and
    nothing to trip over. height: how tall a shaped item stands, in blocks, so the selection box reaches it.
    box, select: the collision and selection boxes as (x1, y1, z1, x2, y2, z2). scale: a shaped item's size on the
    ground (1, its own, by default), or a flat one's (FLAT_SCALE). transform: the whole groundStorageTransform.
    """
    props = {"layout": layout}
    if ctrl:
        props["ctrlKey"] = True
        box, height = box or (0, 0, 0, 0, 0, 0), height or 0.1
    props["collisionBox"] = _cuboid(*(box or (0, 0, 0, 1, 0.125, 1)))
    if select or height:
        props["selectionBox"] = _cuboid(*(select or (0, 0, 0, 1, height, 1)))
    data["behaviors"] = [{"name": "GroundStorable", "properties": props}] + \
        [b for b in data.get("behaviors", []) if b.get("name") != "GroundStorable"]
    flat = not any(k in data for k in ("shape", "shapeByType", "shapebytype"))
    if transform is None and (flat or scale):
        # A flat item is scaled about its middle before the game lays it down; a shaped one about its foot
        transform = {"origin": {"x": 0.5, "y": 0.5 if flat else 0, "z": 0.5}, "scale": scale or FLAT_SCALE[layout]}
    if transform:
        # attributesByType replaces attributes once resolved, so the transform goes in each of its entries
        for attrs in (data["attributesByType"].values() if "attributesByType" in data else [data.setdefault("attributes", {})]):
            attrs["groundStorageTransform"] = transform
    return data


def shape(name, elements):
    keys = set()

    def collect(els):  # (D4) children too: a parent turned about one axis carrying a child turned about another
        for e in els:
            for face in e["faces"].values():
                keys.add(face["texture"][1:])
            collect(e.get("children", ()))
    collect(elements)
    data = {"textureWidth": 16, "textureHeight": 16, "textures": {k: tpath(k) for k in sorted(keys)}, "elements": elements}
    write_json(os.path.join(ASSETS, "shapes", "block", "detail", name + ".json"), data)
    return "block/detail/" + name


def block(code, data, comment=None):
    data = dict({"code": code}, **data)
    write_json(os.path.join(ASSETS, "blocktypes", "detail", code + ".json"), data, comment)


def name(pattern, english):
    LANG["block-" + pattern] = english


def cuboid(box, side=None):
    x1, y1, z1, x2, y2, z2 = box
    c = {"x1": x1, "y1": y1, "z1": z1, "x2": x2, "y2": y2, "z2": z2}
    if side and ROTATE[side]:
        c["rotateY"] = ROTATE[side]
    return c


# ---------------- Props ----------------

def prop(code, english, parts, box=None, oriented=True, material="Wood", sounds=WOOD, light=None, comment=None,
         collide=True, extra=None):
    """A free-standing prop. `parts` is a list of boxes, or {kind: boxes} for a prop with several kinds."""
    data = {}
    kinds = parts if isinstance(parts, dict) else None
    groups = []
    if kinds:
        groups.append({"code": "kind", "states": list(kinds)})
    if oriented:
        groups.append({"code": "side", "states": SIDES})
    if groups:
        data["variantgroups"] = groups

    shapes = {k: shape(f"{code}-{k}", v) for k, v in kinds.items()} if kinds else {None: shape(code, parts)}
    by_type = {}
    for k, path in shapes.items():
        prefix = f"*-{k}" if k else "*"
        if oriented:
            for s in SIDES:
                by_type[f"{prefix}-{s}"] = {"base": path, "rotateY": ROTATE[s]}
        else:
            by_type[prefix if k else "*"] = {"base": path}
    if len(by_type) == 1:
        data["shape"] = next(iter(by_type.values()))
    else:
        data["shapeByType"] = by_type

    first = "*"
    if kinds:
        first = f"*-{next(iter(kinds))}"
    data["creativeinventory"] = {"general": [first + ("-north" if oriented else "")], "decorative": [first + ("-north" if oriented else "")]}
    data.update({"blockmaterial": material, "drawtype": "json", "sidesolid": {"all": False}, "sideopaque": {"all": False},
                 "lightAbsorption": 0, "resistance": 1.5, "sounds": sounds})
    if box is not None:
        if oriented:
            data["collisionboxByType"] = {f"*-{s}": cuboid(box, s) for s in SIDES}
            data["selectionboxByType"] = {f"*-{s}": cuboid(box, s) for s in SIDES}
        else:
            data["collisionbox"] = data["selectionbox"] = cuboid(box)
    if not collide:
        data["collisionbox"] = None
        data.pop("collisionboxByType", None)
    if light:
        data["lightHsv"] = light
    if extra:
        data.update(extra)
    block(code, data, comment or english)
    name(code + "-*" if groups else code, english)


# ---------------- Wall decorations ----------------

class Decor:
    """A decoration on one face of a wall block. `rels` maps the block height above the floor (1 = bottom) to its
    boxes; a decoration spanning several heights becomes one part per height."""

    def __init__(self, code, english, rels, light=None, ambient=None, particles=None, cls=None):
        self.code, self.english, self.rels = code, english, rels
        self.light, self.ambient, self.particles, self.cls = light, ambient, particles, cls

    def parts(self):
        if len(self.rels) == 1:
            rel, els = next(iter(self.rels.items()))
            return [(self.code, rel, els)]
        return [(f"{self.code}{rel}", rel, els) for rel, els in self.rels.items()]


def wall_family(family, english, walls, decors, material="Stone", sounds=STONE, comment=None, textures=None):
    """One block type holding every decoration for one wall material. `walls` maps a height to the wall texture key
    used there (falling back to the highest one given). `textures` (B7) goes into the block type as it is: named
    texture keys of the decorations' shapes given other versions (`alternates`)."""
    states, by_type = [], {}
    light_by, absorb_by, sounds_by, particles_by, class_by, entity_by = {}, {}, {}, {}, {}, {}
    manifest = {}
    for d in decors:
        for state, rel, els in d.parts():
            wall = walls[max([k for k in walls if k <= rel], default=min(walls))]
            path = shape(f"{family}-{state}", [cube(wall)] + els)
            states.append(state)
            for s in SIDES:
                by_type[f"*-{state}-{s}"] = {"base": path, "rotateY": ROTATE[s]}
            manifest.setdefault(d.code, {})[rel] = state
            if d.light:
                light_by[f"*-{state}-*"] = d.light
                absorb_by[f"*-{state}-*"] = 0
            if d.ambient:
                sounds_by[f"*-{state}-*"] = dict(sounds, ambient=d.ambient[0], ambientBlockCount=d.ambient[1])
            if d.particles:
                for s in SIDES:
                    particles_by[f"*-{state}-{s}"] = d.particles(s)
            if d.cls:
                class_by[f"*-{state}-*"] = d.cls[0]
                entity_by[f"*-{state}-*"] = d.cls[1]
            LANG[f"block-{family}-{state}-*"] = d.english
    data = {
        "variantgroups": [{"code": "decor", "states": states}, {"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-north"], "decorative": ["*-north"]},
        "blockmaterial": material, "drawtype": "json", "shapeByType": by_type,
        "lightAbsorption": 99, "resistance": 4, "sounds": sounds,
    }
    if textures:
        data["textures"] = textures
    if light_by:
        data["lightHsvByType"] = light_by
        data["lightAbsorptionByType"] = dict(absorb_by, **{"*": 99})
    if sounds_by:
        data["soundsByType"] = dict(sounds_by, **{"*": sounds})
        data.pop("sounds")
    if particles_by:
        data["particlePropertiesByType"] = particles_by
    if class_by:
        data["classByType"] = class_by
        data["entityClassByType"] = entity_by
    block(family, data, comment or f"{english} with decorations on one face")
    MANIFEST[family] = manifest
