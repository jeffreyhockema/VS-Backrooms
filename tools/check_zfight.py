"""Finds z-fighting candidates in block shapes: faces that the game would draw in the same plane, facing the same way.

Two kinds are reported:

  same shape  two faces of one shape lie in the same plane, face the same way and overlap (a flange's end flush with
              the pipe end it covers, a strut's face on the wall cube's own face, two boxes sharing a top);
  neighbour   a face lies on a block boundary plane with the block *behind* it being a neighbour, not the shape's own
              block (an element reaching out of its block, its face exactly on the next block's face). If that
              neighbour is a full block (a wall, the floor, the ceiling) whose face there shows, the two fight. The
              game culls a shape's boundary faces against an opaque neighbour only when the face lies inside the block's
              own square, so faces outside it are always drawn (decompiled JsonTesselator).

Elements are placed as the game's ShapeTesselator places them (rotation origin, rotationX/Y/Z in that order, scale,
children relative to their parent's "from"), so rotated parts are compared exactly too. Faces closer than --tol pixels
count as one plane; with --near, pairs up to 0.03 px apart are listed separately (they can still fight far away).
Left out unless --hidden: overlaps whose space just in front lies inside another element of the shape, and undersides
at y 0 (they rest on the floor). Pairs drawn with the same texture are left out unless --same-texture. What remains
still needs judging: a top at y 16 under a ceiling or the next part of a tall model never shows, and a "neighbour" face
only fights if that neighbour really is a full block (for a wall block's pipes, that is a face that is not open).

    python tools/check_zfight.py                    # every shape under assets/backrooms/shapes/block
    python tools/check_zfight.py level2 wallpipe    # only shapes whose path contains one of these
    python tools/check_zfight.py --same-texture     # also list pairs drawn with the same texture (usually harmless)
"""
import argparse
import glob
import json
import math
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SHAPES = os.path.join(ROOT, "assets", "backrooms", "shapes")

# (axis, sign) of each face: north -z, east +x, south +z, west -x, up +y, down -y
FACES = {"north": (2, -1), "east": (0, 1), "south": (2, 1), "west": (0, -1), "up": (1, 1), "down": (1, -1)}
DIRNAME = {(0, 1): "east", (0, -1): "west", (1, 1): "up", (1, -1): "down", (2, 1): "south", (2, -1): "north"}


def mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def translate(x, y, z):
    return [[1, 0, 0, x], [0, 1, 0, y], [0, 0, 1, z], [0, 0, 0, 1]]


def rotate(axis, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    if abs(c) < 1e-12:
        c = 0.0
    if abs(s) < 1e-12:
        s = 0.0
    if axis == 0:
        return [[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]]
    if axis == 1:
        return [[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]]
    return [[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def apply(m, p):
    return tuple(m[i][0] * p[0] + m[i][1] * p[1] + m[i][2] * p[2] + m[i][3] for i in range(3))


def element_faces(el, parent, out, path, solids):
    """Appends (shape path, element name, face name, texture, corners, normal) for each face of an element and its
    children, in block pixels, and (inverse transform, lo, hi) of each element's volume to `solids`."""
    frm, to = el.get("from"), el.get("to")
    if not frm or not to:
        return
    o = el.get("rotationOrigin") or [0, 0, 0]
    m = mat_mul(parent, translate(*o))
    for axis, key in ((0, "rotationX"), (1, "rotationY"), (2, "rotationZ")):
        if el.get(key):
            m = mat_mul(m, rotate(axis, el[key]))
    sx, sy, sz = el.get("scaleX", 1), el.get("scaleY", 1), el.get("scaleZ", 1)
    if (sx, sy, sz) != (1, 1, 1):
        m = mat_mul(m, [[sx, 0, 0, 0], [0, sy, 0, 0], [0, 0, sz, 0], [0, 0, 0, 1]])
    m = mat_mul(m, translate(frm[0] - o[0], frm[1] - o[1], frm[2] - o[2]))
    size = [to[i] - frm[i] for i in range(3)]
    lo = [min(0, s) for s in size]
    hi = [max(0, s) for s in size]
    solids.append((invert(m), lo, hi))
    for fname, face in (el.get("faces") or {}).items():
        if fname not in FACES or face is None or face.get("enabled") is False:
            continue
        axis, sign = FACES[fname]
        a, b = (axis + 1) % 3, (axis + 2) % 3
        corners = []
        for ua, ub in ((lo[a], lo[b]), (hi[a], lo[b]), (hi[a], hi[b]), (lo[a], hi[b])):
            p = [0.0, 0.0, 0.0]
            p[axis] = hi[axis] if sign > 0 else lo[axis]
            p[a], p[b] = ua, ub
            corners.append(apply(m, p))
        n0 = [0.0, 0.0, 0.0]
        n0[axis] = sign
        tip = apply(m, n0)
        base = apply(m, (0, 0, 0))
        normal = [tip[i] - base[i] for i in range(3)]
        ln = math.sqrt(sum(c * c for c in normal)) or 1
        normal = tuple(c / ln for c in normal)
        out.append((path, el.get("name", "?"), fname, face.get("texture", ""), corners, normal))
    for child in el.get("children") or []:
        element_faces(child, m, out, path + [el.get("name", "?")], solids)


def invert(m):
    """Inverse of an affine 4x4 matrix."""
    a = [row[:3] for row in m[:3]]
    det = (a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1]) - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
           + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0]))
    if abs(det) < 1e-12:
        return None
    inv = [[0.0] * 3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            r = [k for k in range(3) if k != j]
            c = [k for k in range(3) if k != i]
            minor = a[r[0]][c[0]] * a[r[1]][c[1]] - a[r[0]][c[1]] * a[r[1]][c[0]]
            inv[i][j] = (-1) ** (i + j) * minor / det
    t = [-sum(inv[i][k] * m[k][3] for k in range(3)) for i in range(3)]
    return [inv[0] + [t[0]], inv[1] + [t[1]], inv[2] + [t[2]], [0, 0, 0, 1]]


def shape_faces(shape):
    out, solids = [], []
    ident = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    for el in shape.get("elements") or []:
        element_faces(el, ident, out, [], solids)
    return out, solids


def inside(solids, p, margin=0.005):
    for inv, lo, hi in solids:
        if inv is None:
            continue
        q = apply(inv, p)
        if all(lo[k] + margin < q[k] < hi[k] - margin for k in range(3)):
            return True
    return False


def hidden(solids, poly3d, n):
    """Whether the region just in front of a face (sampled at its centre and towards its corners) lies inside some
    element, so that neither face of a coplanar pair there can be seen."""
    cx = [sum(p[k] for p in poly3d) / len(poly3d) for k in range(3)]
    pts = [cx] + [[cx[k] + 0.9 * (p[k] - cx[k]) for k in range(3)] for p in poly3d]
    return all(inside(solids, [q[k] + 0.02 * n[k] for k in range(3)]) for q in pts)


def plane_basis(n):
    """Two unit vectors spanning the plane with normal n."""
    ref = (1.0, 0.0, 0.0) if abs(n[0]) < 0.9 else (0.0, 1.0, 0.0)
    u = (n[1] * ref[2] - n[2] * ref[1], n[2] * ref[0] - n[0] * ref[2], n[0] * ref[1] - n[1] * ref[0])
    lu = math.sqrt(sum(c * c for c in u))
    u = tuple(c / lu for c in u)
    v = (n[1] * u[2] - n[2] * u[1], n[2] * u[0] - n[0] * u[2], n[0] * u[1] - n[1] * u[0])
    return u, v


def poly_area(p):
    return abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))) / 2


def ccw(p):
    s = sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))
    return p if s >= 0 else p[::-1]


def clip(subject, clipper):
    """Sutherland-Hodgman: the part of convex polygon `subject` inside convex polygon `clipper` (both CCW)."""
    out = subject
    for i in range(len(clipper)):
        a, b = clipper[i], clipper[(i + 1) % len(clipper)]
        inp, out = out, []
        if not inp:
            break

        def inside(p):
            return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= -1e-9

        for j in range(len(inp)):
            p, q = inp[j], inp[(j + 1) % len(inp)]
            pin, qin = inside(p), inside(q)
            if pin:
                out.append(p)
            if pin != qin:
                dx, dy = q[0] - p[0], q[1] - p[1]
                den = (b[0] - a[0]) * dy - (b[1] - a[1]) * dx
                if abs(den) > 1e-12:
                    t = ((b[0] - a[0]) * (a[1] - p[1]) - (b[1] - a[1]) * (a[0] - p[0])) / den
                    out.append((p[0] + t * dx, p[1] + t * dy))
    return out


def overlap(f, g, n):
    """The area two coplanar faces share, and that shared polygon back in 3D (on f's plane)."""
    u, v = plane_basis(n)
    d = sum(f[0][i] * n[i] for i in range(3))
    pf = ccw([(sum(c[i] * u[i] for i in range(3)), sum(c[i] * v[i] for i in range(3))) for c in f])
    pg = ccw([(sum(c[i] * u[i] for i in range(3)), sum(c[i] * v[i] for i in range(3))) for c in g])
    inter = clip(pf, pg)
    if len(inter) < 3:
        return 0.0, []
    return poly_area(inter), [[a * u[i] + b * v[i] + d * n[i] for i in range(3)] for a, b in inter]


def label(face):
    path, name, fname, tex, _, _ = face
    return "/".join(path + [name]) + "." + fname + f" ({tex})"


def on_floor(f):
    """A downward face at y 0: it rests on the block below, so nothing can see it."""
    return f[5][1] < -0.999 and all(abs(c[1]) < 1e-6 for c in f[4])


def check(shape, tol, near, same_texture, min_area, show_hidden=False):
    """Returns (same-shape pairs, near pairs, neighbour faces) for one shape."""
    faces, solids = shape_faces(shape)
    if not show_hidden:
        faces = [f for f in faces if not on_floor(f)]
    groups = {}
    for i, f in enumerate(faces):
        n = f[5]
        d = sum(f[4][0][k] * n[k] for k in range(3))
        key = tuple(round(c, 3) + 0.0 for c in n)
        groups.setdefault(key, []).append((d, i))
    pairs, nears = [], []
    for key, items in groups.items():
        items.sort()
        for x in range(len(items)):
            d1, i = items[x]
            for y in range(x + 1, len(items)):
                d2, j = items[y]
                gap = d2 - d1
                if gap > near:
                    break
                f, g = faces[i], faces[j]
                if f[3] == g[3] and not same_texture:
                    continue
                area, poly = overlap(f[4], g[4], key)
                if area < min_area:
                    continue
                if not show_hidden and hidden(solids, poly, key):
                    continue
                (pairs if gap <= tol else nears).append((gap, area, f, g))
    neighbours = []
    for f in faces:
        n = f[5]
        axis = next((k for k in range(3) if abs(abs(n[k]) - 1) < 1e-6), None)
        if axis is None:
            continue
        d = f[4][0][axis]
        if any(abs(c[axis] - d) > 1e-6 for c in f[4]):
            continue
        plane = round(d / 16) * 16
        gap = (d - plane) * (1 if n[axis] > 0 else -1)  # > 0: in front of the boundary
        if abs(gap) > near:
            continue
        # The blocks behind the face: split it at block edges, each piece lies on the face of the block behind it
        a, b = (axis + 1) % 3, (axis + 2) % 3
        lo_a, hi_a = min(c[a] for c in f[4]), max(c[a] for c in f[4])
        lo_b, hi_b = min(c[b] for c in f[4]), max(c[b] for c in f[4])
        behind = plane // 16 - (1 if n[axis] > 0 else 0)
        for ca in range(math.floor(lo_a / 16), math.ceil(hi_a / 16)):
            for cb in range(math.floor(lo_b / 16), math.ceil(hi_b / 16)):
                pa = (max(lo_a, ca * 16), min(hi_a, ca * 16 + 16))
                pb = (max(lo_b, cb * 16), min(hi_b, cb * 16 + 16))
                if (pa[1] - pa[0]) * (pb[1] - pb[0]) < min_area:
                    continue
                cell = [0, 0, 0]
                cell[axis], cell[a], cell[b] = behind, ca, cb
                cell = tuple(cell)
                if cell == (0, 0, 0):
                    continue
                piece = []
                for ua, ub in ((pa[0], pb[0]), (pa[1], pb[0]), (pa[1], pb[1]), (pa[0], pb[1])):
                    q = [0.0, 0.0, 0.0]
                    q[axis], q[a], q[b] = d, ua, ub
                    piece.append(q)
                if not show_hidden and hidden(solids, piece, n):
                    continue
                neighbours.append((gap, cell, f))
    return pairs, nears, neighbours


def cell_name(cell):
    parts = []
    for k, (neg, pos) in enumerate((("west", "east"), ("below", "above"), ("north", "south"))):
        if cell[k]:
            parts.append(f"{abs(cell[k]) if abs(cell[k]) > 1 else ''}{neg if cell[k] < 0 else pos}")
    return " ".join(parts)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("filters", nargs="*", help="only shapes whose path contains one of these")
    ap.add_argument("--root", default=os.path.join(SHAPES, "block"), help="folder of shapes to scan")
    ap.add_argument("--tol", type=float, default=0.002, help="pixels apart that still count as one plane")
    ap.add_argument("--near", action="store_true", help="also list faces up to 0.03 px apart")
    ap.add_argument("--same-texture", action="store_true", help="also list pairs drawn with the same texture")
    ap.add_argument("--no-neighbour", action="store_true", help="skip faces on a neighbour block's face")
    ap.add_argument("--min-area", type=float, default=0.01, help="smallest overlap reported, in square pixels")
    ap.add_argument("--brief", action="store_true", help="one line per shape")
    ap.add_argument("--hidden", action="store_true",
                    help="also list pairs buried inside another element, and undersides resting on the floor (y 0)")
    args = ap.parse_args()
    near = 0.03 if args.near else args.tol

    paths = sorted(glob.glob(os.path.join(args.root, "**", "*.json"), recursive=True))
    if args.filters:
        paths = [p for p in paths if any(f in p.replace("\\", "/") for f in args.filters)]
    totals = [0, 0, 0, 0]
    for p in paths:
        rel = os.path.relpath(p, args.root).replace("\\", "/")
        try:
            with open(p, encoding="utf-8-sig") as fh:
                shape = json.load(fh)
        except (OSError, ValueError) as e:
            print(f"{rel}: unreadable ({e})")
            continue
        pairs, nears, neighbours = check(shape, args.tol, near, args.same_texture, args.min_area, args.hidden)
        if args.no_neighbour:
            neighbours = []
        if not (pairs or nears or neighbours):
            continue
        totals[0] += 1
        totals[1] += len(pairs)
        totals[2] += len(nears)
        totals[3] += len(neighbours)
        if args.brief:
            print(f"{rel}: {len(pairs)} same-shape, {len(nears)} near, {len(neighbours)} on a neighbour's face")
            continue
        print(rel)
        for gap, area, f, g in pairs:
            print(f"  same plane  {area:6.2f} px2  {label(f)}  /  {label(g)}")
        for gap, area, f, g in nears:
            print(f"  near {gap:.3f}  {area:6.2f} px2  {label(f)}  /  {label(g)}")
        byside = {}
        for gap, cell, f in neighbours:
            facing = DIRNAME[next((k, 1 if f[5][k] > 0 else -1) for k in range(3) if abs(f[5][k]) > 0.5)]
            where = "on" if abs(gap) <= args.tol else f"{gap:+.3f} px off"
            byside.setdefault((cell, facing, where), []).append(f)
        for (cell, facing, where), fs in byside.items():
            names = ", ".join(label(f) for f in fs[:4]) + (f", ... ({len(fs)} faces)" if len(fs) > 4 else "")
            print(f"  neighbour   {facing}-facing, {where} the {facing} face of the block {cell_name(cell)}: {names}")
    print(f"{len(paths)} shapes scanned; {totals[0]} with candidates: {totals[1]} same-shape pairs, {totals[2]} near pairs, "
          f"{totals[3]} faces on a neighbour's face")
    return 0


if __name__ == "__main__":
    sys.exit(main())
