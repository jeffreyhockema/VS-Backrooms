"""The Hub's rounded tunnels (layout version 9): the curved vault pieces and the table the world generator reads.

Called by tools/gen_hub.py after the tunnel blocks. The lore's tunnels (Wikidot's photo, a French road tunnel; Fandom's
photos) are vaulted: straight walls up to about two thirds of the height, then the concrete curves over into the roof.
In layout version 9 the Hub's tunnels are built that way:

- main tunnels (13 wide): straight walls up to rel 6 (over the sigils on rel 5), then a quarter round of radius 4 each
  side up to a flat crown 5 blocks wide at rel 10 (air up to rel 9), where the jet fans and lane signals hang;
- side tunnels (7 wide): straight walls up to rel 6, then a half round of radius 3.5, its crown at rel 9.5.

Each cell the curve passes through holds a piece of `hub-vault-{piece}-{side}`: the cell's part above the curve, cut
in 1 px steps (a staircase of boxes, one box per run of pixel columns with the same height), extruded along the
tunnel, in the tunnel roof's concrete (`hub-ceiling`'s texture). `side` is the way toward the tunnel's middle (the
model is drawn with the wall to the south). Cells wholly above the curve are full roof blocks (`hub-ceiling`), cells
below it air. The generator chooses per column from WorldLayout.HubVault (WorldLayout.HubVault.g.cs, written here):
where tunnels meet, a cell is air if any tunnel through it leaves it air, and a cell two tunnels both cut takes the
piece that leaves more air, so junctions open into each other with nothing left hanging.

Also in layout version 9, from the lore's photos: the white edge line along each side of the road, painted on the asphalt
beside the kerb (`hub-asphalt-edge-{side}`, the line on the block's `side` edge, toward the kerb), and the sidewalk's
rounded kerb (`hub-curb`, built before but never placed) along a straight wall.

A piece claims an opaque side only where its geometry covers that whole face (the wall side when its first pixel
column is solid to the floor of the cell, the top when every column reaches the top), so nothing is ever culled
against a face that is not there.
"""
import math
import os
import random

from PIL import Image

import gen_hub_kit as K

SPRING = 6  # the rel the walls end and the curve begins (the sigils are on rel 5)
FROM, TOP = 6, 10  # the rels the vault table covers (the cells above TOP are always solid)


def main_surface(x):
    """The underside of a main tunnel's roof over a point |x| blocks from its middle line (rel units)."""
    ax = abs(x)
    if ax <= 2.5:
        return 10.0
    dx = min(ax - 2.5, 4.0)
    return SPRING + math.sqrt(max(0.0, 16.0 - dx * dx))


def side_surface(x):
    """The underside of a side tunnel's roof: a half round of radius 3.5 on the springline."""
    ax = min(abs(x), 3.5)
    return SPRING + math.sqrt(max(0.0, 3.5 * 3.5 - ax * ax))


PROFILES = (("m", 6, main_surface), ("s", 3, side_surface))


def heights(surface, c, rel):
    """The cell's sixteen pixel columns, from its wall side (i = 0) to the middle: where the solid begins in each
    (0 = solid from the cell's floor, 16 = all air). Column c > 0 has its wall at x = c + 0.5."""
    out = []
    for i in range(16):
        x = abs(c) + 0.5 - (i + 0.5) / 16
        h = round((surface(x) - rel) * 16)
        out.append(max(0, min(16, h)))
    return tuple(out)


def piece_elements(hs):
    """The boxes of a piece: the wall to the south (z = 16), the middle to the north; pixel column i spans
    z 15 - i .. 16 - i. One box per run of columns of the same height, solid from that height to the top; only the
    faces that can show (the underside, the step toward the middle or the wall where it is higher, the ends, the top)."""
    runs = []
    for i, h in enumerate(hs):
        if h >= 16:
            continue
        if runs and runs[-1][2] == h and runs[-1][1] == i:
            runs[-1][1] = i + 1
        else:
            runs.append([i, i + 1, h])
    els = []
    for n, (i0, i1, h) in enumerate(runs):
        z1, z2 = 16 - i1, 16 - i0
        before = hs[i0 - 1] if i0 > 0 else None  # the column on the wall side
        after = hs[i1] if i1 < 16 else 16  # the column on the middle side
        faces = ["down", "east", "west", "up"]
        if after > h:  # the step toward the middle shows (the next column is lower in solid)
            faces.append("north")
        if before is None or before > h:  # the wall side: the block's own face, or a step up toward the wall
            faces.append("south")
        els.append(K.bx(f"Step{n}", (0, h, z1), (16, 16, z2), "ceiling", faces=tuple(faces)))
    return els


def collision_boxes(hs, side):
    """Four boxes roughly following the curve (each over four pixel columns, from their mean height)."""
    out = []
    for g in range(4):
        cols = hs[g * 4:g * 4 + 4]
        solid = [h for h in cols if h < 16]
        if not solid:
            continue
        y1 = round(sum(solid) / len(solid)) / 16
        z1, z2 = (16 - (g + 1) * 4) / 16, (16 - g * 4) / 16
        out.append(K.cuboid((0, y1, z1, 1, 1, z2), side))
    return out


OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east"}


def edge_lines():
    """Asphalt with a white edge line along one side (5 px of 32 wide, 3 px in from the edge), painted on each of the
    road's three versions: worn paint over the aggregate, even all along so it runs on unbroken from block to block."""
    keys = []
    for k, key in enumerate(("asphalt-plain", "asphalt-plain-2", "asphalt-plain-3")):
        path = os.path.join(K.ASSETS, "textures", "block", "hub", key + ".png")
        src = Image.open(path).convert("RGBA")
        for side in K.SIDES:
            img = src.copy()
            p = img.load()
            rng = random.Random(K.seed_of(f"hubedge{k}{side}"))
            for a in range(K.S):
                for b in range(3, 8):  # b: pixels in from the kerb edge
                    x, y = {"north": (a, b), "south": (a, K.S - 1 - b), "west": (b, a), "east": (K.S - 1 - b, a)}[side]
                    r, g, bl, al = p[x, y]
                    paint = (196, 192, 178)
                    m = 0.78 + rng.uniform(-0.08, 0.06) - (0.10 if b in (3, 7) else 0)
                    p[x, y] = tuple(int(round(c * (1 - m) + q * m)) for c, q in zip((r, g, bl), paint)) + (al,)
            name = f"asphalt-edge-{side}" + ("" if k == 0 else f"-{k + 1}")
            K.save_tex(img, name)
            keys.append((side, name))
    by_type = {}
    for side in K.SIDES:
        names = [n for s, n in keys if s == side]
        up = {"base": "block/hub/" + names[0], "alternates": [{"base": "block/hub/" + n} for n in names[1:]]}
        by_type[f"*-{side}"] = {"all": K.versions_of("asphalt-plain"), "up": up}
    K.block("hub-asphalt-edge", {
        "variantgroups": [{"code": "side", "states": K.SIDES}],
        "creativeinventory": {"general": ["*-north"], "construction": ["*-north"]},
        "blockmaterial": "Stone", "drawtype": "cube", "texturesByType": by_type,
        "lightAbsorption": 99, "resistance": 4, "sounds": K.STONE,
    }, "(Layout version 9) asphalt with the road's white edge line along its side edge (toward the kerb)")
    K.name("hub-asphalt-edge-*", "Asphalt with Edge Line")


LINE_KINDS = ("ns", "we", "ne", "es", "sw", "wn", "givewayns", "givewaywe")


def road_lines():
    """(Layout version 11) the road's markings, painted on each of the road's three versions like the edge line:
    - the yellow middle line of a big tunnel's two lanes, 4 px of 32 wide in the middle of the block, so it sits on the
      middle of the carriageway's middle block: straight (ns: running north-south, we) and round a corner (ne joins
      the north side's middle to the east side's, on a quarter circle round the block's north-east corner; es, sw, wn
      the same turned), so it runs on unbroken round the bends;
    - the broken white give-way line across a narrow tunnel where it comes out into another (givewayns: across a
      tunnel running north-south, so the paint runs east-west; givewaywe), a dash 22 px long with gaps between blocks.
    The north side of a texture is its top row, as for the edge line."""
    yellow, white = (214, 168, 46), (200, 196, 182)
    S = K.S
    for k, key in enumerate(("asphalt-plain", "asphalt-plain-2", "asphalt-plain-3")):
        src = Image.open(os.path.join(K.ASSETS, "textures", "block", "hub", key + ".png")).convert("RGBA")
        for kind in LINE_KINDS:
            img = src.copy()
            p = img.load()
            rng = random.Random(K.seed_of(f"hubline{k}{kind}"))
            corner = {"ne": (S, 0), "es": (S, S), "sw": (0, S), "wn": (0, 0)}.get(kind)
            for y in range(S):
                for x in range(S):
                    cx, cy = x + 0.5, y + 0.5
                    if kind == "ns":
                        d, paint = abs(cx - S / 2), yellow
                    elif kind == "we":
                        d, paint = abs(cy - S / 2), yellow
                    elif corner:
                        d, paint = abs(math.hypot(cx - corner[0], cy - corner[1]) - S / 2), yellow
                    elif kind == "givewayns":
                        d, paint = (abs(cy - S / 2) if 5 <= x < 27 else 99), white
                    else:
                        d, paint = (abs(cx - S / 2) if 5 <= y < 27 else 99), white
                    if d >= 2.5:
                        continue
                    r, g, bl, al = p[x, y]
                    m = 0.8 + rng.uniform(-0.08, 0.06) - (0.25 if d > 1.8 else 0.1 if d > 1.2 else 0)
                    p[x, y] = tuple(int(round(c * (1 - m) + q * m)) for c, q in zip((r, g, bl), paint)) + (al,)
            K.save_tex(img, f"asphalt-line-{kind}" + ("" if k == 0 else f"-{k + 1}"))
    by_type = {}
    for kind in LINE_KINDS:
        names = [f"asphalt-line-{kind}"] + [f"asphalt-line-{kind}-{k}" for k in (2, 3)]
        up = {"base": "block/hub/" + names[0], "alternates": [{"base": "block/hub/" + n} for n in names[1:]]}
        by_type[f"*-{kind}"] = {"all": K.versions_of("asphalt-plain"), "up": up}
    K.block("hub-asphalt-line", {
        "variantgroups": [{"code": "kind", "states": list(LINE_KINDS)}],
        "creativeinventory": {"general": ["*-ns"], "construction": ["*-ns"]},
        "blockmaterial": "Stone", "drawtype": "cube", "texturesByType": by_type,
        "lightAbsorption": 99, "resistance": 4, "sounds": K.STONE,
    }, "(Layout version 11) asphalt with the road's markings: the yellow middle line (straight or round a corner) and the white give-way line")
    K.name("hub-asphalt-line-*", "Asphalt with Road Marking")


def generate(csharp_path=None):
    edge_lines()
    road_lines()
    pieces = {}  # name -> heights
    tables = {}
    for tag, half, surface in PROFILES:
        rows = []
        for c in range(half + 1):
            row = []
            for rel in range(FROM, TOP + 1):
                hs = heights(surface, c, rel)
                if all(h >= 16 for h in hs):
                    row.append("air")
                elif all(h == 0 for h in hs):
                    row.append("solid")
                else:
                    nm = f"{tag}{c}r{rel}"
                    pieces[nm] = hs
                    row.append(nm)
            rows.append(row)
        tables[tag] = rows

    names = list(pieces)
    shape_of = {}
    for nm in names:
        shape_of[nm] = K.shape(f"vault-{nm}", piece_elements(pieces[nm]))
    by_type, opaque, solid, boxes = {}, {}, {}, {}
    for nm in names:
        hs = pieces[nm]
        wall_full = hs[0] == 0
        top_full = all(h < 16 for h in hs)
        for s in K.SIDES:
            key = f"*-{nm}-{s}"
            by_type[key] = {"base": shape_of[nm], "rotateY": K.ROTATE[s]}
            faces = {"all": False, OPPOSITE[s]: wall_full, "up": top_full}
            opaque[key] = faces
            solid[key] = dict(faces)
            boxes[key] = collision_boxes(hs, s)
    K.block("hub-vault", {
        "variantgroups": [{"code": "piece", "states": names}, {"code": "side", "states": K.SIDES}],
        "creativeinventory": {"general": [f"*-{names[0]}-north"], "construction": [f"*-{names[0]}-north"]},
        "blockmaterial": "Stone", "drawtype": "json", "shapeByType": by_type,
        "textures": {"ceiling": K.versions_of("ceiling")},
        "sideopaqueByType": opaque, "sidesolidByType": solid, "lightAbsorption": 99, "resistance": 6,
        "sounds": K.STONE, "collisionSelectionBoxesByType": boxes,
    }, "(Layout version 9) the Hub's tunnel roof where it curves over from the walls: the part of a cell above the curve,"
       " in 1 px steps, the wall to the south of the -north variant (side: the way toward the tunnel's middle). m: main"
       " tunnels (quarter rounds of radius 4 up to a flat crown), s: side tunnels (a half round of radius 3.5); the digit"
       " is the column's distance from the middle line, r the rel above the floor")
    K.name("hub-vault-*", "Concrete Tunnel Vault")

    if csharp_path:
        write_table(csharp_path, names, pieces, tables)
    return names, pieces, tables


def write_table(path, names, pieces, tables):
    index = {"air": 0, "solid": 1}
    for i, nm in enumerate(names):
        index[nm] = i + 2
    air = [0, 0] + [sum(pieces[nm]) for nm in names]  # how much of the cell's cross-section is open, in px * px
    lines = ["// Generated by tools/gen_hub_vault.py (bash tools/locked.sh run python tools/gen_hub.py): do not edit.",
             "namespace Backrooms.Worldgen;", "",
             "public sealed partial class WorldLayout", "{",
             f"    /// <summary>The rels the Hub's vault table covers in layout version 9 (above <see cref=\"HubVaultTop\"/> is solid).</summary>",
             f"    public const int HubVaultFrom = {FROM}, HubVaultTop = {TOP};", "",
             "    /// <summary>The vault pieces by index (0 air, 1 solid): the piece state of hub-vault-{piece}-{side}.</summary>",
             "    public static readonly string[] HubVaultPieces = { \"\", \"\", " + ", ".join(f"\"{nm}\"" for nm in names) + " };", "",
             "    /// <summary>How much of each piece's cross-section is open (px * px of 256): where two tunnels cut one cell, the more open wins.</summary>",
             "    private static readonly short[] HubVaultOpen = { " + ", ".join(str(a) for a in air) + " };", ""]
    for tag, field, what in (("m", "HubVaultMain", "a main tunnel"), ("s", "HubVaultSide", "a side tunnel")):
        rows = tables[tag]
        lines.append(f"    /// <summary>The vault of {what}: [distance from its middle line, rel - HubVaultFrom].</summary>")
        lines.append(f"    private static readonly byte[,] {field} =")
        lines.append("    {")
        for c, row in enumerate(rows):
            lines.append("        { " + ", ".join(str(index[v]) for v in row) + " }," + f" // {c}: " + " ".join(row))
        lines.append("    };")
        lines.append("")
    lines[-1] = "}"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    # The hub blocks' texture alternates come from the B15 painters (gen_hub_kit.VERSIONS), which only gen_hub.py runs
    # first: on its own this would write the vault and the asphalt edge without them. Run through gen_hub.py instead.
    if not K.VERSIONS:
        K.b15_textures()
        print("note: gen_hub.py is the full Hub generator; the B15 textures were repainted so the alternates are kept")
    names, pieces, tables = generate()
    for tag in tables:
        for c, row in enumerate(tables[tag]):
            print(tag, c, row)
