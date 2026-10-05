"""Renders rough isometric previews of block shapes (seen from the north-west, above) to check proportions.

    python tools/preview_shapes.py out.png shapes/block/detail/desk.json ...   (globs allowed)
Each face is filled with the average colour of its texture, darkened by its facing.
"""
import glob
import json
import math
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets")
_colours = {}


def tex_colour(path):
    if path not in _colours:
        domain, rel = path.split(":") if ":" in path else ("backrooms", path)
        f = os.path.join(ASSETS, domain, "textures", rel + ".png")
        try:
            im = Image.open(f).convert("RGBA").resize((1, 1), Image.BOX)
            _colours[path] = im.getpixel((0, 0))[:3]
        except OSError:
            _colours[path] = (255, 0, 255)
    return _colours[path]


def rotate(p, origin, rx, ry, rz):
    x, y, z = p[0] - origin[0], p[1] - origin[1], p[2] - origin[2]
    if rx:
        a = math.radians(rx)
        y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
    if ry:
        a = math.radians(ry)
        x, z = x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)
    if rz:
        a = math.radians(rz)
        x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
    return (x + origin[0], y + origin[1], z + origin[2])


FACES = {"north": ((0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0)), "south": ((0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 1)),
         "west": ((0, 1, 0), (0, 1, 1), (0, 0, 1), (0, 0, 0)), "east": ((1, 1, 0), (1, 1, 1), (1, 0, 1), (1, 0, 0)),
         "up": ((0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)), "down": ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1))}
NORMALS = {"north": (0, 0, -1), "south": (0, 0, 1), "west": (-1, 0, 0), "east": (1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}
VIEW = (-math.cos(math.radians(30)) / math.sqrt(2), math.sin(math.radians(30)), -math.cos(math.radians(30)) / math.sqrt(2))
SHADE = {"north": 0.85, "south": 0.5, "west": 0.68, "east": 0.6, "up": 1.0, "down": 0.4}


def project(p, scale, cx, cy):
    # Camera to the north-west, above, looking south-east and down 30 degrees: fronts (north faces) and west sides show
    x, y, z = p[0] - 8, p[1], p[2] - 8
    h = (x + z) / math.sqrt(2)
    b = math.radians(30)
    sx = (z - x) / math.sqrt(2)
    sy = y * math.cos(b) + h * math.sin(b)
    depth = y * math.sin(b) - h * math.cos(b)
    return cx + sx * scale, cy - sy * scale, depth


def render(shape_path, size=200):
    data = json.load(open(shape_path, encoding="utf-8"))
    tex = data.get("textures", {})
    polys = []
    for el in data["elements"]:
        f0, t0 = el["from"], el["to"]
        origin = el.get("rotationOrigin", [8, 8, 8])
        rx, ry, rz = el.get("rotationX", 0), el.get("rotationY", 0), el.get("rotationZ", 0)
        for face, info in el["faces"].items():
            corners = []
            for c in FACES[face]:
                p = tuple(f0[i] + (t0[i] - f0[i]) * c[i] for i in range(3))
                corners.append(rotate(p, origin, rx, ry, rz))
            n = rotate(NORMALS[face], (0, 0, 0), rx, ry, rz)
            if n[0] * VIEW[0] + n[1] * VIEW[1] + n[2] * VIEW[2] <= 0.01:
                continue  # facing away from the camera
            col = tex_colour(tex.get(info["texture"][1:], "?"))
            k = SHADE[face] if not info.get("glow") else 1.1
            polys.append((corners, tuple(min(255, int(v * k)) for v in col)))
    img = Image.new("RGBA", (size, size), (40, 44, 48, 255))
    d = ImageDraw.Draw(img)
    scale = size / 44
    pts = []
    for corners, col in polys:
        pr = [project(c, scale, size / 2, size * 0.78) for c in corners]
        pts.append((sum(p[2] for p in pr) / 4, [(p[0], p[1]) for p in pr], col))
    for _, poly, col in sorted(pts, key=lambda t: t[0]):
        d.polygon(poly, fill=col + (255,), outline=(20, 20, 20, 255))
    # ground grid of the block's own footprint
    g = [project(p, scale, size / 2, size * 0.78) for p in ((0, 0, 0), (16, 0, 0), (16, 0, 16), (0, 0, 16))]
    d.polygon([(p[0], p[1]) for p in g], outline=(120, 200, 120, 255))
    return img


if __name__ == "__main__":
    out = sys.argv[1]
    files = []
    for pattern in sys.argv[2:]:
        files += sorted(glob.glob(os.path.join(ASSETS, "backrooms", pattern)))
    cols = 8
    cell = 200
    sheet = Image.new("RGBA", (cols * cell, ((len(files) + cols - 1) // cols) * (cell + 14)), (30, 30, 30, 255))
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(files):
        x, y = (i % cols) * cell, (i // cols) * (cell + 14)
        sheet.alpha_composite(render(f, cell), (x, y))
        d.text((x + 3, y + cell), os.path.basename(f)[:-5][:30], fill=(255, 255, 255, 255))
    sheet.save(out)
    print(len(files), "shapes")
