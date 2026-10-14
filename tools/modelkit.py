"""Model helpers for the graphics pass: bevels, insets, panels, door and cabinet hardware, dials, grilles, keypads,
legs, rims and a small furniture kit, as geometry rather than paint.

Element format. Every helper returns a list of shape elements, the same dicts `detail_kit.bx` and `gen_shapes.box`
make: {"name", "from", "to", "faces": {dir: {"texture": "#key", "uv": [...]}}} plus rotationOrigin/rotationX/Y/Z
where a part is turned. They follow `detail_kit.bx`'s convention because it is the superset (rotation, explicit
UVs) and because most furniture is a detail prop: block space is 0-16 per axis, a prop's front faces north (-Z,
low z), and each face's UV is taken from its own size (capped at 16), so a texture keeps its 32 px-per-block scale
on parts of any size. The lists can go straight into `detail_kit.shape()`, `detail_kit.prop()`, `gen_shapes.save()`
or a far level's own writer, mixed with their own boxes, and `detail_kit.turn` / `gen_shapes.rot` work on them
(use this module's `turn` for parts with a rotation, which those two do not carry round).

Texture keys. A `tex` argument is either one key (every face) or a dict by role:
    {"top": k, "side": k, "front": k, "back": k, "bottom": k, "all": k}
front is the north face, back south, side east and west, top up, bottom down; a role left out falls back to
"side", and "side" to "all". Composite helpers (chair, table, cabinet, door) take one such spec per part and default
to separate keys for top, side and front, so the blocktype can give each its own material. That is the point: a
blocktype's `textures: { all: ... }` overrides every key of its shape (README section 9), so a prop whose seat top
and legs share one key can never get two materials. Name keys after the material, not the part.

Sizes. Thin parts are at least 0.5 units (1 texture px) in every visible dimension, and nothing a helper makes lies
in the same plane as another of its faces facing the same way, except where that overlap is buried inside a third
element (check with tools/check_zfight.py --root <folder of the shapes>).
"""
import json
import math

DIRS = ("north", "east", "south", "west", "up", "down")
ROLE = {"north": "front", "south": "back", "east": "side", "west": "side", "up": "top", "down": "bottom"}
PX = 0.5  # one texture pixel in shape units (32 px textures over 16 units)


# ---------------- Basics ----------------

def texmap(tex):
    """A tex spec (one key, or a dict by role or by face) as {face: key}."""
    if isinstance(tex, str):
        return {f: tex for f in DIRS}
    allk = tex.get("all")
    side = tex.get("side", allk)
    out = {}
    for f in DIRS:
        k = tex.get(f) or tex.get(ROLE[f]) or side
        if k is None:
            raise ValueError(f"no texture for the {f} face in {tex}")
        out[f] = k
    return out


def mat(top=None, side=None, front=None, back=None, bottom=None, all=None):
    """A tex spec by role, leaving out what is not given."""
    return {k: v for k, v in (("top", top), ("side", side), ("front", front), ("back", back), ("bottom", bottom),
                              ("all", all)) if v is not None}


def box(name, frm, to, tex, faces=DIRS, glow=0, rot=None, origin=None, uv=None):
    """One box, as detail_kit.bx, but with a texture key per face from a tex spec. `rot` is (x, y, z) degrees about
    `origin` (the box centre by default); `uv` fixes every face's UV."""
    (x1, y1, z1), (x2, y2, z2) = frm, to
    assert x2 > x1 and y2 > y1 and z2 > z1, (name, frm, to)
    w, h, d = x2 - x1, y2 - y1, z2 - z1
    sizes = {"north": (w, h), "south": (w, h), "east": (d, h), "west": (d, h), "up": (w, d), "down": (w, d)}
    keys = texmap(tex)
    out = {}
    for f in faces:
        a, b = sizes[f]
        face = {"texture": "#" + keys[f], "uv": list(uv) if uv else [0, 0, round(min(16, max(a, PX)), 4), round(min(16, max(b, PX)), 4)]}
        if glow:
            face["glow"] = glow
        out[f] = face
    el = {"name": name, "from": [round(v, 4) for v in (x1, y1, z1)], "to": [round(v, 4) for v in (x2, y2, z2)], "faces": out}
    if rot:
        el["rotationOrigin"] = [round(v, 4) for v in (origin or ((x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2))]
        for axis, v in zip("XYZ", rot):
            if v:
                el["rotation" + axis] = v
    return el


def without(faces, *drop):
    return tuple(f for f in faces if f not in drop)


def turn(els, times):
    """Turns elements 90 degrees clockwise seen from above about the block centre, `times` times (north -> east),
    carrying rotation origins and single-axis rotations round with them."""
    els = json.loads(json.dumps(els))
    for _ in range(times % 4):
        for el in els:
            (x1, y1, z1), (x2, y2, z2) = el["from"], el["to"]
            el["from"], el["to"] = [16 - z2, y1, x1], [16 - z1, y2, x2]
            f = el["faces"]
            el["faces"] = {k: v for k, v in {"east": f.get("north"), "south": f.get("east"), "west": f.get("south"),
                                             "north": f.get("west"), "up": f.get("up"), "down": f.get("down")}.items() if v is not None}
            if "rotationOrigin" in el:
                ox, oy, oz = el["rotationOrigin"]
                el["rotationOrigin"] = [16 - oz, oy, ox]
                rx, rz = el.pop("rotationX", 0), el.pop("rotationZ", 0)
                assert not (rx and rz), "turn handles one tilt axis at a time"
                if rx:
                    el["rotationZ"] = rx
                if rz:
                    el["rotationX"] = -rz
    return els


def move(els, dx=0.0, dy=0.0, dz=0.0):
    els = json.loads(json.dumps(els))
    for e in els:
        e["from"] = [round(e["from"][0] + dx, 4), round(e["from"][1] + dy, 4), round(e["from"][2] + dz, 4)]
        e["to"] = [round(e["to"][0] + dx, 4), round(e["to"][1] + dy, 4), round(e["to"][2] + dz, 4)]
        if "rotationOrigin" in e:
            o = e["rotationOrigin"]
            e["rotationOrigin"] = [round(o[0] + dx, 4), round(o[1] + dy, 4), round(o[2] + dz, 4)]
    return els


def textures(els):
    """The texture keys a list of elements uses, for a shape's "textures" table."""
    return sorted({f["texture"][1:] for e in els for f in e["faces"].values()})


# ---------------- Bevels, insets, panels ----------------

def bevelled_box(name, frm, to, tex, b=PX):
    """A box with all twelve edges stepped in by `b` (one texture px by default): three overlapping boxes, each full
    length along one axis and inset by b on the other two. The game lights the steps' tops and darkens their
    undersides, so the edge reads as a bevel without painting one. Where two of the boxes share a plane the overlap
    lies inside the third, so nothing fights."""
    (x1, y1, z1), (x2, y2, z2) = frm, to
    assert min(x2 - x1, y2 - y1, z2 - z1) > 2 * b, (name, "too small for its bevel")
    return [
        box(name + "Z", (x1 + b, y1 + b, z1), (x2 - b, y2 - b, z2), tex),
        box(name + "X", (x1, y1 + b, z1 + b), (x2, y2 - b, z2 - b), tex),
        box(name + "Y", (x1 + b, y1, z1 + b), (x2 - b, y2, z2 - b), tex),
    ]


def _cuts(a, b, n, bar):
    """n openings between a and b, separated by bars of width `bar`: [(lo, hi), ...]."""
    span = (b - a - (n - 1) * bar) / n
    return [(a + i * (span + bar), a + i * (span + bar) + span) for i in range(n)]


def frame_members(name, x1, y1, x2, y2, z1, z2, border, tex, grid=(1, 1), mid=None):
    """Rails (full width) and stiles (between the rails) of a frame round a grid of openings, from z1 to z2. Returns
    (elements, openings). `mid` is the width of the inner muntins and mid rails (border by default)."""
    mid = border if mid is None else mid
    cols, rows = grid
    els = []
    xs = _cuts(x1 + border, x2 - border, cols, mid)
    ys = _cuts(y1 + border, y2 - border, rows, mid)
    # rails: bottom, top and the mid rails, all full width
    rails = [(y1, y1 + border), (y2 - border, y2)] + [(ys[i][1], ys[i + 1][0]) for i in range(rows - 1)]
    for i, (a, b) in enumerate(rails):
        els.append(box(f"{name}Rail{i}", (x1, a, z1), (x2, b, z2), tex))
    # stiles: left, right and the muntins, in each row of openings, between the rails
    for j, (ya, yb) in enumerate(ys):
        stiles = [(x1, x1 + border), (x2 - border, x2)] + [(xs[i][1], xs[i + 1][0]) for i in range(cols - 1)]
        for i, (a, b) in enumerate(stiles):
            els.append(box(f"{name}Stile{j}_{i}", (a, ya, z1), (b, yb, z2), tex, faces=without(DIRS, "up", "down")))
    openings = [(xa, ya, xb, yb) for (ya, yb) in ys for (xa, xb) in xs]
    return els, openings


def inset_panel(name, frm, to, tex, panel=None, border=1.5, depth=PX, grid=(1, 1), mid=None):
    """A solid box whose front (north) face has recessed panels: a frame of rails and stiles `depth` proud of a
    panel face, round a grid of (cols, rows) openings. For cabinet fronts, wainscot, drawer banks, machine panels.
    `tex` is the body and frame; `panel` (default: the same) is what shows in the recesses. Returns elements; the
    openings are (x1, y1, x2, y2) in `inset_panel.openings` of the last call, for placing handles."""
    (x1, y1, z1), (x2, y2, z2) = frm, to
    body = box(name + "Body", (x1, y1, z1 + depth), (x2, y2, z2), _with_front(tex, panel))
    frame, openings = frame_members(name, x1, y1, x2, y2, z1, z1 + depth, border, _front_as_side(tex), grid, mid)
    for e in frame:
        e["faces"].pop("south", None)  # against the body
    inset_panel.openings = openings
    return [body] + frame


def _with_front(tex, panel):
    m = texmap(tex)
    if panel:
        m["north"] = texmap(panel)["north"]
    return m


def _front_as_side(tex):
    """The frame of a panel shows the front material on its front and on the sides lining the recess."""
    m = texmap(tex)
    return {f: (m["north"] if f in ("north", "east", "west", "up", "down") else m[f]) for f in DIRS}


def frame_and_panel(name, frm, to, tex, panel=None, border=2.0, depth=PX, grid=(1, 2), raised=0.0, mid=None,
                    both_sides=True):
    """A door leaf or a cabinet door: a frame of rails and stiles the full thickness, round panels set back `depth`
    from the front (and from the back with both_sides). raised > 0 adds a fielded panel standing `raised` proud of
    each panel, one border in from its edges. grid is (cols, rows) of panels. Returns elements; the panel openings
    are in `frame_and_panel.openings`."""
    (x1, y1, z1), (x2, y2, z2) = frm, to
    assert z2 - z1 >= 2 * depth + PX if both_sides else z2 - z1 >= depth + PX, (name, "too thin for its panels")
    els, openings = frame_members(name, x1, y1, x2, y2, z1, z2, border, tex, grid, mid)
    pz1, pz2 = z1 + depth, (z2 - depth if both_sides else z2)
    ptex = panel or tex
    for i, (a, b, c, d) in enumerate(openings):
        els.append(box(f"{name}Panel{i}", (a, b, pz1), (c, d, pz2), ptex, faces=("north", "south")))
        if raised:
            f = min(border, (c - a) / 4, (d - b) / 4)
            els.append(box(f"{name}Field{i}", (a + f, b + f, pz1 - raised), (c - f, d - f, pz1), ptex,
                           faces=without(DIRS, "south")))
            if both_sides:
                els.append(box(f"{name}FieldB{i}", (a + f, b + f, pz2), (c - f, d - f, pz2 + raised), ptex,
                               faces=without(DIRS, "north")))
    frame_and_panel.openings = openings
    return els


def inset_window(name, x1, y1, x2, y2, z1, z2, frame, glass="glass", bead=PX, depth=PX):
    """A glazed opening through a door or panel from z1 to z2: a 1 px bead round it on both faces, standing `bead`
    wide and `depth` proud, and the pane in the middle of the thickness. The caller leaves the opening out of the
    leaf (build the leaf with frame_and_panel and use one of its openings). glass is a key; it needs the
    Transparent render pass on its blocktype to show as glass."""
    zc = (z1 + z2) / 2
    els = [box(name + "Pane", (x1, y1, zc - PX / 2), (x2, y2, zc + PX / 2), glass, faces=("north", "south"))]
    for side, (za, zb) in (("F", (z1 - depth, z1)), ("B", (z2, z2 + depth))):
        els += [box(f"{name}Bead{side}T", (x1, y2 - bead, za), (x2, y2, zb), frame),
                box(f"{name}Bead{side}B", (x1, y1, za), (x2, y1 + bead, zb), frame),
                box(f"{name}Bead{side}L", (x1, y1 + bead, za), (x1 + bead, y2 - bead, zb), frame, faces=without(DIRS, "up", "down")),
                box(f"{name}Bead{side}R", (x2 - bead, y1 + bead, za), (x2, y2 - bead, zb), frame, faces=without(DIRS, "up", "down"))]
    # the reveal: the opening's own sides through the leaf
    els += [box(name + "RevealT", (x1, y2, z1), (x2, y2 + PX, z2), frame, faces=("down",)),
            box(name + "RevealB", (x1, y1 - PX, z1), (x2, y1, z2), frame, faces=("up",))]
    return els


# ---------------- Hardware ----------------

def handle(name, x, y, z, length=4.0, axis="y", standoff=1.0, thick=PX * 2, tex="metal"):
    """A bar pull on a front face at z (sticking out toward -z): a bar `length` long along `axis` ("x" or "y"),
    centred on (x, y), `standoff` off the face on two posts."""
    t = thick / 2
    zb1, zb2 = z - standoff - thick, z - standoff
    if axis == "y":
        bar = box(name + "Bar", (x - t, y - length / 2, zb1), (x + t, y + length / 2, zb2), tex)
        posts = [box(name + "Post" + str(i), (x - t * 0.8, py - t * 0.8, zb2), (x + t * 0.8, py + t * 0.8, z), tex,
                     faces=without(DIRS, "south", "north")) for i, py in enumerate((y - length / 2 + t, y + length / 2 - t))]
    else:
        bar = box(name + "Bar", (x - length / 2, y - t, zb1), (x + length / 2, y + t, zb2), tex)
        posts = [box(name + "Post" + str(i), (px_ - t * 0.8, y - t * 0.8, zb2), (px_ + t * 0.8, y + t * 0.8, z), tex,
                     faces=without(DIRS, "south", "north")) for i, px_ in enumerate((x - length / 2 + t, x + length / 2 - t))]
    return [bar] + posts


def lever(name, x, y, z, length=3.0, tex="metal", side=1):
    """A lever door handle on a front face at z: a round-ish rose plate, a short neck, and the lever reaching
    `length` toward +x (side=1) or -x (side=-1)."""
    els = [box(name + "Rose", (x - 1, y - 1, z - PX), (x + 1, y + 1, z), tex, faces=without(DIRS, "south")),
           box(name + "Neck", (x - PX / 2 - 0.25, y - PX / 2 - 0.25, z - 1.5), (x + PX / 2 + 0.25, y + PX / 2 + 0.25, z - PX), tex,
               faces=without(DIRS, "south", "north"))]
    a, b = (x - 0.5, x - 0.5 + length) if side > 0 else (x + 0.5 - length, x + 0.5)
    els.append(box(name + "Lever", (a, y - PX, z - 2.0), (b, y + PX, z - 1.5), tex))
    return els


def knob(name, x, y, z, r=1.0, depth=1.5, tex="metal"):
    """A knob on a front face at z: a thin rose, a neck, and a bevelled head of half-size r."""
    els = [box(name + "Rose", (x - r * 0.9, y - r * 0.9, z - PX / 2), (x + r * 0.9, y + r * 0.9, z), tex, faces=without(DIRS, "south")),
           box(name + "Neck", (x - r * 0.4, y - r * 0.4, z - depth + r), (x + r * 0.4, y + r * 0.4, z - PX / 2), tex,
               faces=without(DIRS, "south", "north"))]
    b = PX / 2 if r < 1.5 else PX
    return els + bevelled_box(name + "Head", (x - r, y - r, z - depth - r * 0.2), (x + r, y + r, z - depth + r), tex, b)


def hinge(name, x, y1, y2, z, tex="metal", knuckles=2, leaf=1.5, side="left"):
    """A butt hinge at a door's edge x on a front face at z: a leaf plate 0.25 proud on the face and a knuckle
    standing proud of the edge, split into `knuckles` barrels with a 1 px gap, with a pin cap on top."""
    s = 1 if side == "left" else -1
    lx1, lx2 = sorted((x, x + s * leaf))
    els = [box(name + "Leaf", (lx1, y1, z - 0.25), (lx2, y2, z), tex, faces=without(DIRS, "south"))]
    kx1, kx2 = x - 0.5, x + 0.5
    gap = PX
    span = (y2 - y1 - (knuckles - 1) * gap) / knuckles
    for i in range(knuckles):
        a = y1 + i * (span + gap)
        els.append(box(f"{name}Knuckle{i}", (kx1, a, z - 1.0), (kx2, a + span, z), tex))
    els.append(box(name + "Pin", (x - 0.25, y2, z - 0.75), (x + 0.25, y2 + PX, z - 0.25), tex))
    return els


def push_bar(name, x1, x2, y, z, tex="metal", bar_tex=None, depth=2.0):
    """A panic bar across a door's front at z: two end housings `depth` deep and a bar between them a little lower
    and nearer the face, as on a fire door. bar_tex lets the bar be a different finish."""
    bt = bar_tex or tex
    hw = 1.5
    els = [box(name + "HousingL", (x1, y - 1.25, z - depth), (x1 + hw, y + 1.25, z), tex, faces=without(DIRS, "south")),
           box(name + "HousingR", (x2 - hw, y - 1.25, z - depth), (x2, y + 1.25, z), tex, faces=without(DIRS, "south")),
           box(name + "Bar", (x1 + hw, y - 0.75, z - depth + 0.25), (x2 - hw, y + 0.5, z - 0.5), bt, faces=without(DIRS, "east", "west", "south"))]
    return els


def kick_plate(name, x1, x2, y1, y2, z, tex="metal", t=0.25, screws=True):
    """A metal plate at the foot of a door's front at z, `t` proud, with a screw head (1 px) in each corner."""
    els = [box(name, (x1, y1, z - t), (x2, y2, z), tex, faces=without(DIRS, "south", "down"))]
    if screws:
        for i, (sx, sy) in enumerate(((x1 + 0.5, y1 + 0.5), (x2 - 1.0, y1 + 0.5), (x1 + 0.5, y2 - 1.0), (x2 - 1.0, y2 - 1.0))):
            els.append(box(f"{name}Screw{i}", (sx, sy, z - t - 0.15), (sx + PX, sy + PX, z - t), tex, faces=without(DIRS, "south")))
    return els


def grille(name, frm, to, tex, bars=5, axis="v", bar=PX, frame=1.0, back="dark", bar_tex=None):
    """A vent, fan or speaker grille: a frame round an opening on the front (north) of the box frm..to, `bars` bars
    across it along `axis` ("v" upright, "h" level, "grid" both) set a little behind the frame's face, and a dark
    backing at the back of the box."""
    (x1, y1, z1), (x2, y2, z2) = frm, to
    bt = bar_tex or tex
    fr, openings = frame_members(name, x1, y1, x2, y2, z1, z2, frame, tex)
    ox1, oy1, ox2, oy2 = openings[0]
    els = fr + [box(name + "Back", (ox1, oy1, z2 - PX), (ox2, oy2, z2), back, faces=("north",))]
    bz1, bz2 = z1 + 0.25, z1 + 0.25 + max(PX, min(1.0, (z2 - z1) / 3))
    if axis in ("v", "grid"):
        for i in range(bars):
            cx = ox1 + (ox2 - ox1) * (i + 1) / (bars + 1)
            els.append(box(f"{name}BarV{i}", (cx - bar / 2, oy1, bz1), (cx + bar / 2, oy2, bz2), bt, faces=without(DIRS, "up", "down")))
    if axis in ("h", "grid"):
        for i in range(bars):
            cy = oy1 + (oy2 - oy1) * (i + 1) / (bars + 1)
            z_off = 0.1 if axis == "grid" else 0.0  # crossing bars: not in one plane
            els.append(box(f"{name}BarH{i}", (ox1, cy - bar / 2, bz1 + z_off), (ox2, cy + bar / 2, bz2 + z_off), bt,
                           faces=without(DIRS, "east", "west")))
    return els


def dial(name, cx, cy, z, r=2.5, angle=-40.0, face="dialface", bezel="metal", needle="needle", glass=None):
    """A dial on a front face at z: the face (a painted scale is fine: that is printing, not relief) set back in an
    octagonal bezel ring standing 1 px proud, a needle at `angle` degrees from straight up (clockwise as seen from
    the front), a hub cap over its pivot, and optionally a glass key over it all (Transparent render pass needed)."""
    els = [box(name + "Face", (cx - r, cy - r, z - 0.1), (cx + r, cy + r, z), face, faces=("north",), uv=[0, 0, 16, 16])]
    t = PX
    s8 = 0.828 * r  # side of a regular octagon whose flats are r from the centre
    straight = [((cx - s8 / 2 - t / 2, cy + r - t), (cx + s8 / 2 + t / 2, cy + r)), ((cx - s8 / 2 - t / 2, cy - r), (cx + s8 / 2 + t / 2, cy - r + t)),
                ((cx - r, cy - s8 / 2 - t / 2), (cx - r + t, cy + s8 / 2 + t / 2)), ((cx + r - t, cy - s8 / 2 - t / 2), (cx + r, cy + s8 / 2 + t / 2))]
    for i, ((a, b), (c, d)) in enumerate(straight):
        els.append(box(f"{name}Bezel{i}", (a, b, z - 1.0), (c, d, z), bezel, faces=without(DIRS, "south")))
    # the four diagonal sides, turned 45 degrees about their own centres and set 0.1 back, so where they overlap the
    # straight ones their fronts are not in the same plane
    m = (r - t / 2) / math.sqrt(2)
    for i, (sx, sy) in enumerate(((1, 1), (-1, 1), (1, -1), (-1, -1))):
        ox, oy = cx + sx * m, cy + sy * m
        els.append(box(f"{name}BezelD{i}", (ox - s8 / 2 - t / 2, oy - t / 2, z - 0.9), (ox + s8 / 2 + t / 2, oy + t / 2, z - 0.05), bezel,
                       faces=without(DIRS, "south"), rot=(0, 0, -45 * sx * sy), origin=(ox, oy, z)))
    L = r * 0.8
    els.append(box(name + "Needle", (cx - 0.25, cy - L * 0.2, z - 0.35), (cx + 0.25, cy + L, z - 0.2), needle,
                   faces=("north", "east", "west", "up"), rot=(0, 0, angle), origin=(cx, cy, z)))
    els.append(box(name + "Hub", (cx - PX, cy - PX, z - 0.6), (cx + PX, cy + PX, z - 0.35), bezel, faces=without(DIRS, "south")))
    if glass:
        els.append(box(name + "Glass", (cx - r + t, cy - r + t, z - 0.8), (cx + r - t, cy + r - t, z - 0.75), glass, faces=("north",)))
    return els


def gauge(name, cx, cy, z, r=2.5, angle=-40.0, face="dialface", body="metal", needle="needle", glass=None,
          depth=1.5, stem=True):
    """A pressure gauge on a wall or cabinet face at z: a bevelled body `depth` deep, the dial on its front, and
    with `stem` a short pipe stub dropping from its underside to the face."""
    zf = z - depth
    els = bevelled_box(name + "Body", (cx - r, cy - r, zf), (cx + r, cy + r, z), body)
    els += dial(name, cx, cy, zf, r, angle, face, body, needle, glass)
    if stem:
        els.append(box(name + "Stem", (cx - PX, cy - r - 2.0, zf + 0.25), (cx + PX, cy - r, zf + 1.25), body,
                       faces=without(DIRS, "up", "south")))
    return els


def keypad(name, x1, y1, z, cols=3, rows=4, key=1.0, gap=PX, border=PX, plate="keypadplate", keys="key"):
    """A keypad on a front face at z, its lower left corner at (x1, y1): a plate 1 px proud and a grid of keys
    standing a further 0.35 proud."""
    w = border * 2 + cols * key + (cols - 1) * gap
    h = border * 2 + rows * key + (rows - 1) * gap
    els = [box(name + "Plate", (x1, y1, z - PX), (x1 + w, y1 + h, z), plate, faces=without(DIRS, "south"))]
    for j in range(rows):
        for i in range(cols):
            a, b = x1 + border + i * (key + gap), y1 + border + j * (key + gap)
            els.append(box(f"{name}Key{j}_{i}", (a, b, z - PX - 0.35), (a + key, b + key, z - PX), keys, faces=without(DIRS, "south")))
    return els


def leg(name, x, z, y1, y2, t=1.0, tex="leg", foot=0.0, taper=0.0):
    """A square leg of thickness t centred on (x, z), from y1 to y2; foot > 0 puts a slightly wider glide or ferrule
    of that height under it; taper > 0 makes its lower half that much thinner."""
    els = []
    yb = y1
    if foot:
        f = t / 2 + 0.25
        els.append(box(name + "Foot", (x - f, y1, z - f), (x + f, y1 + foot, z + f), tex))
        yb = y1 + foot
    if taper:
        ym = (yb + y2) / 2
        ht = (t - taper) / 2
        els.append(box(name + "Low", (x - ht, yb, z - ht), (x + ht, ym, z + ht), tex, faces=without(DIRS, "up", "down") if foot else without(DIRS, "up")))
        els.append(box(name, (x - t / 2, ym, z - t / 2), (x + t / 2, y2, z + t / 2), tex))
    else:
        els.append(box(name, (x - t / 2, yb, z - t / 2), (x + t / 2, y2, z + t / 2), tex, faces=without(DIRS, "down") if foot else DIRS))
    return els


def rim(name, frm, to, tex, w=PX, h=PX, inside=False):
    """A raised lip round the top of the box frm..to: four strips `w` wide and `h` high standing on its top (on its
    outer edge, or one w in with inside=True), as on a tray, a counter or a table edge."""
    (x1, y1, z1), (x2, y2, z2) = frm, to
    if inside:
        x1, z1, x2, z2 = x1 + w, z1 + w, x2 - w, z2 - w
    y = y2
    return [box(name + "N", (x1, y, z1), (x2, y + h, z1 + w), tex, faces=without(DIRS, "down")),
            box(name + "S", (x1, y, z2 - w), (x2, y + h, z2), tex, faces=without(DIRS, "down")),
            box(name + "W", (x1, y, z1 + w), (x1 + w, y + h, z2 - w), tex, faces=without(DIRS, "down", "north", "south")),
            box(name + "E", (x2 - w, y, z1 + w), (x2, y + h, z2 - w), tex, faces=without(DIRS, "down", "north", "south"))]


# ---------------- Furniture ----------------

def chair(name="Chair", x=8.0, z=8.0, w=9.0, d=9.0, seat_h=7.0, back_h=8.0, leg_t=1.0, seat_t=1.5,
          seat=None, frame="chairframe", back=None, back_style="panel", foot=0.0):
    """A chair facing north centred on (x, z): four legs of thickness leg_t (the back pair running up as the back
    posts), a bevelled seat seat_t thick standing on a rail frame, and a back of `back_style` "panel" (an upholstered
    or plywood panel between the posts), "slats" (three upright slats and a top rail) or "none" (a stool).
    seat defaults to {"top": "chairseat", "side": "chairseatside"}; back to the seat's top key on its front and the
    frame's on its other faces."""
    seat = seat or {"top": "chairseat", "side": "chairseatside"}
    sm = texmap(seat)
    back = back or {"front": sm["up"], "back": sm["north"], "side": frame, "top": frame}
    x1, x2, z1, z2 = x - w / 2, x + w / 2, z - d / 2, z + d / 2
    h = leg_t / 2
    els = []
    for i, (lx, lz) in enumerate(((x1 + h, z1 + h), (x2 - h, z1 + h))):
        els += leg(f"{name}LegF{i}", lx, lz, 0, seat_h - seat_t, leg_t, frame, foot)
    top = seat_h + (back_h if back_style != "none" else 0)
    for i, lx in enumerate((x1 + h, x2 - h)):
        els += leg(f"{name}LegB{i}", lx, z2 - h, 0, top, leg_t, frame, foot)
    # rails under the seat, between the legs, set in so they do not share the legs' faces
    ry1, ry2 = seat_h - seat_t - 1.5, seat_h - seat_t
    els.append(box(name + "RailF", (x1 + leg_t, ry1, z1 + 0.25), (x2 - leg_t, ry2, z1 + 0.25 + PX), frame, faces=without(DIRS, "east", "west")))
    els.append(box(name + "RailL", (x1 + 0.25, ry1, z1 + leg_t), (x1 + 0.25 + PX, ry2, z2 - leg_t), frame, faces=without(DIRS, "north", "south")))
    els.append(box(name + "RailR", (x2 - 0.25 - PX, ry1, z1 + leg_t), (x2 - 0.25, ry2, z2 - leg_t), frame, faces=without(DIRS, "north", "south")))
    els += bevelled_box(name + "Seat", (x1 - 0.25, seat_h - seat_t, z1 - 0.25), (x2 + 0.25, seat_h, z2 - leg_t), seat, PX / 2 * 1)
    if back_style == "panel":
        els += bevelled_box(name + "Back", (x1 + leg_t, seat_h + 1.5, z2 - leg_t - 0.25), (x2 - leg_t, top - 0.5, z2 - 0.25), back, PX / 2)
    elif back_style == "slats":
        els.append(box(name + "TopRail", (x1 + leg_t, top - 2.0, z2 - leg_t + 0.25), (x2 - leg_t, top - 0.25, z2 - 0.25), frame))
        inner = _cuts(x1 + leg_t, x2 - leg_t, 4, 1.0)
        for i in range(3):
            a = inner[i][1]
            els.append(box(f"{name}Slat{i}", (a, seat_h + 0.5, z2 - h - 0.25), (a + 1.0, top - 2.0, z2 - h + 0.25), frame,
                           faces=without(DIRS, "up", "down")))
    return els


def table(name="Table", x1=1.0, z1=1.0, x2=15.0, z2=15.0, h=12.0, top_t=1.0, lip=1.0, leg_t=1.5, apron=2.0,
          overhang=1.0, top=None, legs="tableleg", apron_tex=None, foot=0.0):
    """A table: a top top_t thick with a distinct top face and edge, a lip (a band `lip` deep under the top's edge,
    set in 0.5, so the edge reads thicker than the top), an apron of boards `apron` deep under the lip between the
    legs, and four legs of leg_t, set in by `overhang` from the top's edge. top defaults to
    {"top": "tabletop", "side": "tableedge"}."""
    top = top or {"top": "tabletop", "side": "tableedge"}
    tm = texmap(top)
    edge = tm["north"]
    at = apron_tex or edge
    els = [box(name + "Top", (x1, h - top_t, z1), (x2, h, z2), top)]
    li = 0.5
    if lip:
        ly1, ly2 = h - top_t - lip, h - top_t
        els += [box(name + "LipN", (x1 + li, ly1, z1 + li), (x2 - li, ly2, z1 + li + PX), edge, faces=without(DIRS, "up", "south")),
                box(name + "LipS", (x1 + li, ly1, z2 - li - PX), (x2 - li, ly2, z2 - li), edge, faces=without(DIRS, "up", "north")),
                box(name + "LipW", (x1 + li, ly1, z1 + li + PX), (x1 + li + PX, ly2, z2 - li - PX), edge, faces=("west", "down", "east")),
                box(name + "LipE", (x2 - li - PX, ly1, z1 + li + PX), (x2 - li, ly2, z2 - li - PX), edge, faces=("east", "down", "west"))]
    lx1, lx2, lz1, lz2 = x1 + overhang, x2 - overhang, z1 + overhang, z2 - overhang
    ab = h - top_t  # legs and apron run up to the underside of the top, inside the lip
    hl = leg_t / 2
    for i, (lx, lz) in enumerate(((lx1 + hl, lz1 + hl), (lx2 - hl, lz1 + hl), (lx1 + hl, lz2 - hl), (lx2 - hl, lz2 - hl))):
        els += leg(f"{name}Leg{i}", lx, lz, 0, ab, leg_t, legs, foot)
    if apron:
        ay1 = ab - (lip or 0) - apron
        inset_ = 0.25
        els += [box(name + "ApronN", (lx1 + leg_t, ay1, lz1 + inset_), (lx2 - leg_t, ab, lz1 + inset_ + PX), at, faces=without(DIRS, "up", "east", "west")),
                box(name + "ApronS", (lx1 + leg_t, ay1, lz2 - inset_ - PX), (lx2 - leg_t, ab, lz2 - inset_), at, faces=without(DIRS, "up", "east", "west")),
                box(name + "ApronW", (lx1 + inset_, ay1, lz1 + leg_t), (lx1 + inset_ + PX, ab, lz2 - leg_t), at, faces=without(DIRS, "up", "north", "south")),
                box(name + "ApronE", (lx2 - inset_ - PX, ay1, lz1 + leg_t), (lx2 - inset_, ab, lz2 - leg_t), at, faces=without(DIRS, "up", "north", "south"))]
    return els


def cabinet(name="Cabinet", x1=1.0, x2=15.0, z1=4.0, z2=15.0, h=15.0, plinth=1.5, body=None, door=None,
            handle_tex="metal", doors=2, drawers=0, top=None):
    """A floor cabinet facing north: a recessed plinth, a body, `drawers` drawer fronts over `doors` doors (each an
    inset panel with a bar handle) and a top slab overhanging 0.5 at the front and sides with its own top face.
    body/door/top are tex specs; door defaults to {"front": "cabinetdoor", "side": "cabinetbody"}."""
    body = body or {"side": "cabinetbody", "front": "cabinetbody"}
    door = door or {"front": "cabinetdoor", "side": "cabinetbody"}
    top = top or {"top": "cabinettop", "side": "cabinetbody"}
    bm = texmap(body)
    els = [box(name + "Plinth", (x1 + 0.5, 0, z1 + 1.0), (x2 - 0.5, plinth, z2), bm["north"], faces=without(DIRS, "down", "up")),
           box(name + "Body", (x1, plinth, z1 + PX), (x2, h - 1.0, z2), body, faces=without(DIRS, "up"))]
    els.append(box(name + "Top", (x1 - 0.5, h - 1.0, z1 - 0.5), (x2 + 0.5, h, z2), top))
    y = h - 1.0
    fronts = []
    gap = 0.25
    for i in range(drawers):
        fronts.append(("Drawer" + str(i), x1, y - 3.0, x2, y))
        y -= 3.0
    if doors:
        w = (x2 - x1) / doors
        for i in range(doors):
            fronts.append(("Door" + str(i), x1 + i * w, plinth, x1 + (i + 1) * w, y))
    for (n, a, b, c, d) in fronts:
        a2, c2, d2 = a + gap / 2, c - gap / 2, d - gap / 2
        els += inset_panel(name + n, (a2, b, z1), (c2, d2, z1 + PX + 0.01), door, border=1.0, depth=0.25)
        cx = (a2 + c2) / 2
        if n.startswith("Drawer"):
            els += handle(name + n + "H", cx, (b + d2) / 2, z1, 3.0, "x", 0.75, PX, handle_tex)
        else:
            hx = c2 - 1.25 if (n.endswith("0") and doors > 1) else a2 + 1.25
            if doors == 1:
                hx = c2 - 1.25
            els += handle(name + n + "H", hx, (b + d2) / 2 + 1.5, z1, 3.0, "y", 0.75, PX, handle_tex)
    return els


def door(name="Door", x1=1.0, x2=15.0, y2=32.0, z1=7.0, z2=8.75, leaf=None, frame="doorframe", hardware="metal",
         panels=(1, 2), window=False, push=False, kick=True, raised=0.5):
    """A door seen from its push side (north) in a frame: casing posts and a head round the opening, a leaf of
    frame_and_panel with `panels`, hinges on the left, a lever (or a push bar with push=True), a kick plate, and
    with `window` the top panel glazed (an inset_window, glass key "glass"). Spans two blocks high by default
    (y up to 32); split it per block as the level's door code does."""
    leaf = leaf or {"front": "doorleaf", "side": "doorleafedge"}
    cw = 1.25
    lx1, lx2 = x1 + cw, x2 - cw
    els = [box(name + "CasingL", (x1, 0, z1 - PX), (lx1, y2, z2 + PX), frame, faces=without(DIRS, "down", "up")),
           box(name + "CasingR", (lx2, 0, z1 - PX), (x2, y2, z2 + PX), frame, faces=without(DIRS, "down", "up")),
           box(name + "Head", (lx1, y2 - cw, z1 - PX), (lx2, y2, z2 + PX), frame, faces=without(DIRS, "east", "west", "up"))]
    ly2 = y2 - cw
    leaf_els = frame_and_panel(name + "Leaf", (lx1 + 0.1, 0.1, z1), (lx2 - 0.1, ly2 - 0.1, z2), leaf, border=2.0, depth=0.5,
                               grid=panels, raised=0 if window else raised)
    openings = frame_and_panel.openings
    if window:
        top = max(openings, key=lambda o: o[3])
        leaf_els = [e for e in leaf_els if not (e["name"].startswith(name + "LeafPanel") and openings[int(e["name"][len(name + "LeafPanel"):])] == top)]
        a, b, c, d = top
        els += inset_window(name + "Win", a, b, c, d, z1, z2, texmap(leaf)["north"])
    els += leaf_els
    els += hinge(name + "HingeT", lx1 + 0.1, ly2 - 5.0, ly2 - 2.0, z1, hardware)
    els += hinge(name + "HingeB", lx1 + 0.1, 3.0, 6.0, z1, hardware)
    if push:
        els += push_bar(name + "Push", lx1 + 1.0, lx2 - 1.0, 15.0, z1, hardware)
    else:
        els += lever(name + "Lever", lx2 - 2.0, 15.0, z1, 3.0, hardware, side=-1)
    if kick:
        els += kick_plate(name + "Kick", lx1 + 0.75, lx2 - 0.75, 0.5, 3.5, z1, hardware)
    return els
