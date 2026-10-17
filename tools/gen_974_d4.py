"""Level 974, Kitty's House, graphics pass D4: a bevel and inset pass on the furniture bodies. B16 carried them at C+
("only the paint changed"): their boxes were sharp-edged slabs, and drawer fronts flat plates on the carcass. Here, at
the end of each builder in gen_974.furniture (behind `gen_974.D4_FURNITURE`), named boxes are swapped for
`modelkit.bevelled_box`es (each edge stepped in by a fraction of a pixel, so the game lights a rim on top and darkens
one under it), cushions and mattresses get a softer, deeper bevel, and drawer and door fronts a raised field inside a
margin, so they read as made furniture rather than slabs. Codes, variants, footprints, collision boxes, textures and
colours do not change; every part keeps its place and size (a bevel only steps the edges in).

    refine(els, spec, fields=())
        spec:   {element name: bevel} for the boxes to bevel (rotated parts are left as they are);
        fields: names of front plates (facing north) to give a raised field.

Revert: set gen_974.D4_FURNITURE to False.
"""
import modelkit as K

CUSHION = 0.45   # cushions, pillows, the mattress: a soft, deep bevel
BOARD = 0.25     # tops, seats, rails, posts
THIN = 0.15      # drawer fronts and thin plates (a front is 0.4 thick)


def _tex(el):
    keys = {f["texture"].lstrip("#") for f in el["faces"].values()}
    return keys.pop() if len(keys) == 1 else None


def _run(el, b, axis):
    """A bar that runs on into the next block along `axis` (a bed's rails and mattress, a banquette's seat): only the
    four edges along the axis are stepped, so no groove shows where it meets its other half. Three boxes that do not
    overlap: the core, full across one way, and a strip on each side of it inset by b."""
    (x1, y1, z1), (x2, y2, z2) = el["from"], el["to"]
    tex = _tex(el)
    faces = set(el["faces"])
    if axis == "z":
        parts = [((x1, y1 + b, z1), (x2, y2 - b, z2)), ((x1 + b, y2 - b, z1), (x2 - b, y2, z2)),
                 ((x1 + b, y1, z1), (x2 - b, y1 + b, z2))]
    else:
        parts = [((x1, y1 + b, z1), (x2, y2 - b, z2)), ((x1, y2 - b, z1 + b), (x2, y2, z2 - b)),
                 ((x1, y1, z1 + b), (x2, y1 + b, z2 - b))]
    out = []
    for i, (a, c) in enumerate(parts):
        e = K.box(el["name"] + "R" + str(i), a, c, tex)
        e["faces"] = {f: v for f, v in e["faces"].items() if f in faces}
        if e["faces"]:
            out.append(e)
    return out


def _bevel(el, b):
    (x1, y1, z1), (x2, y2, z2) = el["from"], el["to"]
    tex = _tex(el)
    axis = None
    if isinstance(b, tuple):
        b, axis = b
    if tex is None or "rotationOrigin" in el or min(x2 - x1, y2 - y1, z2 - z1) <= 2 * b + 0.05:
        return [el]
    if axis:
        return _run(el, b, axis)
    faces = set(el["faces"])
    out = []
    for part in K.bevelled_box(el["name"], (x1, y1, z1), (x2, y2, z2), tex, b=b):
        part["faces"] = {f: v for f, v in part["faces"].items() if f in faces}
        if part["faces"]:
            out.append(part)
    return out


def _field(el, margin=0.8, proud=0.2):
    """A raised field on a north-facing front plate: a box `proud` out of its face, `margin` in from its edges."""
    (x1, y1, z1), (x2, y2, z2) = el["from"], el["to"]
    tex = _tex(el)
    m = min(margin, (x2 - x1) / 4, (y2 - y1) / 4)
    if tex is None or x2 - x1 - 2 * m < 0.5 or y2 - y1 - 2 * m < 0.5:
        return []
    return [K.box(el["name"] + "Field", (x1 + m, y1 + m, z1 - proud), (x2 - m, y2 - m, z1), tex,
                  faces=("north", "east", "west", "up", "down"))]


def refine(els, spec, fields=()):
    out = []
    for el in els:
        name = el.get("name")
        if name in fields:
            out += _field(el)
        if name in spec:
            out += _bevel(el, spec[name])
        else:
            out.append(el)
    return out


# The specs, per builder (element names as gen_974 builds them)
# (The bed is two blocks: its side rails and mattress run on from the head block into the foot block along z)
BED_HEAD = dict({f"Post{x}": BOARD for x in (0, 14.4)}, **{f"Finial{x}": 0.3 for x in (0, 14.4)},
                TopRail=BOARD, LowRail=BOARD, RailL=(BOARD, "z"), RailR=(BOARD, "z"), Mattress=(CUSHION, "z"), Fold=0.4,
                PillowL=CUSHION, PillowR=CUSHION)
BED_FEET = dict({f"Post{x}": BOARD for x in (0, 14.4)}, **{f"Finial{x}": 0.3 for x in (0, 14.4)},
                TopRail=BOARD, LowRail=BOARD, RailL=(BOARD, "z"), RailR=(BOARD, "z"), Mattress=(CUSHION, "z"))
NIGHTSTAND = {"Body": BOARD, "Top": BOARD, "Drawer": THIN}
NIGHTSTAND_FIELDS = ("Drawer",)
DESK = dict({"Top": BOARD, "PanelL": BOARD, "Pedestal": BOARD, "Modesty": BOARD},
            **{f"Drawer{i}": THIN for i in range(3)})
DESK_FIELDS = tuple(f"Drawer{i}" for i in range(3))
CHAIR_DESK = {"Seat": CUSHION, "SeatEdge": 0.3, "Back": CUSHION, "BackTop": 0.3, "Post": BOARD}
CHAIR_DINING = {"Seat": BOARD, "Cushion": CUSHION, "PostL": BOARD, "PostR": BOARD, "TopRail": BOARD,
                "Slat1": 0.2, "Slat2": 0.2}
DRESSER = dict({"Body": BOARD, "Top": BOARD, "Plinth": BOARD}, **{f"Drawer{i}": THIN for i in range(3)})
DRESSER_FIELDS = tuple(f"Drawer{i}" for i in range(3))
TABLE = {"Top": BOARD, "Apron": BOARD}
# (Banquettes stand in runs along x; a corner's side arm runs on along z)
BANQUETTE = {"Seat": (CUSHION, "x"), "Cap": (BOARD, "x"), "BackCushion": (CUSHION, "x"),
             "SeatN": (CUSHION, "z"), "SideCap": (BOARD, "z"), "SideCushion": (CUSHION, "z")}
