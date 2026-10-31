"""Renders an item shape the way the game's inventory slot does, from the item type's guiTransform.

    python tools/preview_item_gui.py out.png itemtypes/almondwater.json [more item types ...] [--rot X,Y,Z] [--size 256]

The GUI draws items with the screen's y axis pointing down, and (unlike blocks, which get 180 added to the x rotation)
applies guiTransform.rotation as written, so an item whose guiTransform has the usual block value x = -22.6 stands on
its head. This reproduces the client's matrix (translate origin + translation, scale, Rx, Ry, Rz, translate -origin) with
a painter's-order flat-shaded draw, and with --rot draws the same item with another rotation next to it.
"""
import json
import math
import os
import re
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import preview_shapes as ps  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")


def loose_json(path):
    text = open(path, encoding="utf-8").read()
    text = re.sub(r"^\s*//.*$", "", text, flags=re.M)
    text = re.sub(r"(?m)([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1"\2":', text)
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return json.loads(text)


def rot(p, rx, ry, rz, order="xyz"):
    x, y, z = p
    # the matrix is Rx * Ry * Rz, so a point is turned by Rz first
    a = math.radians(rz)
    x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
    a = math.radians(ry)
    x, z = x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)
    a = math.radians(rx)
    y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
    return x, y, z


def draw(shape_file, transform, size, extra_x=0.0):
    data = json.load(open(shape_file, encoding="utf-8"))
    tex = data.get("textures", {})
    o = transform.get("origin", {"x": 0.5, "y": 0.5, "z": 0.5})
    r = transform.get("rotation", {"x": 0, "y": 0, "z": 0})
    s = transform.get("scale", 1)
    img = Image.new("RGBA", (size, size), (52, 52, 56, 255))
    d = ImageDraw.Draw(img)
    faces = []
    for el, chain in ps.walk(data["elements"]):
        f0, t0 = el["from"], el["to"]
        for face, info in el.get("faces", {}).items():
            if face not in ps.FACES or "texture" not in info:
                continue
            quad = []
            for c in ps.FACES[face]:
                p = [(f0[i] + (t0[i] - f0[i]) * c[i]) / 16 for i in range(3)]
                p = [p[0] - o["x"], p[1] - o["y"], p[2] - o["z"]]
                p = rot(p, r["x"] + extra_x, r["y"], r["z"])
                quad.append(p)
            # screen: x right, y down; z grows away from the viewer for the draw order
            n = ps.orient(ps.NORMALS[face], el, chain)
            n = rot(n, r["x"] + extra_x, r["y"], r["z"])
            if n[2] < -0.01:
                continue
            path = tex.get(info["texture"].lstrip("#"), "?")
            faces.append((sum(q[2] for q in quad) / 4, quad, path, info.get("uv") or ps.auto_uv(face, f0, t0), n))
    k = size * 0.38 * s / 2.2
    for _, quad, path, uv, n in sorted(faces, key=lambda t: t[0]):
        poly = [(size / 2 + q[0] * k, size / 2 + q[1] * k) for q in quad]
        im = ps.tex_image(path)
        col = ps.tex_colour(path)
        if im is not None:
            u = [(uv[0] + uv[2]) / 2, (uv[1] + uv[3]) / 2]
            col = im.getpixel((int(u[0]) % im.width, int(u[1]) % im.height))[:3]
        shade = 0.6 + 0.4 * max(0, n[2])
        d.polygon(poly, fill=tuple(min(255, int(c * shade)) for c in col), outline=(20, 20, 20))
    return img


if __name__ == "__main__":
    args = sys.argv[1:]
    out = args.pop(0)
    size, alt = 256, None
    if "--size" in args:
        i = args.index("--size")
        size = int(args[i + 1])
        del args[i:i + 2]
    if "--rot" in args:
        i = args.index("--rot")
        alt = [float(v) for v in args[i + 1].split(",")]
        del args[i:i + 2]
    sheet = Image.new("RGBA", (size * 2 * len(args), size + 16), (30, 30, 30, 255))
    sd = ImageDraw.Draw(sheet)
    for n, f in enumerate(args):
        item = loose_json(os.path.join(ROOT, "assets", "backrooms", f))
        shape = os.path.join(ROOT, "assets", "backrooms", "shapes", item["shape"]["base"] + ".json")
        t = item["guiTransform"]
        sheet.paste(draw(shape, t, size), (n * 2 * size, 0))
        sd.text((n * 2 * size + 4, size + 2), "as in the file: rotation %s" % t["rotation"], fill=(255, 255, 255, 255))
        if alt:
            t2 = dict(t, rotation={"x": alt[0], "y": alt[1], "z": alt[2]})
            sheet.paste(draw(shape, t2, size), ((n * 2 + 1) * size, 0))
            sd.text(((n * 2 + 1) * size + 4, size + 2), "rotation %s" % t2["rotation"], fill=(255, 255, 255, 255))
    sheet.save(out)
