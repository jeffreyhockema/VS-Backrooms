"""Renders a Vintage Story entity shape (with its texture) in its animations, the way the game composes them:
element = translate(pivot) . rotate X, Y, Z . stretch . translate(from + offset - pivot), children nested.

    python entrender.py shape.json texture.png out.png [anims=walk,idle] [frames=4] [frame=N] [scale=8] [yoff=px] [views=side,front,34]
"""
import json
import math
import sys

import numpy as np
from PIL import Image, ImageDraw

FACE_CORNERS = {
    # corners in order with uv (0,1),(1,1),(1,0),(0,0): bottom-left, bottom-right, top-right, top-left seen from outside
    "north": [(1, 0, 0), (0, 0, 0), (0, 1, 0), (1, 1, 0)],
    "south": [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)],
    "west": [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)],
    "east": [(1, 0, 1), (1, 0, 0), (1, 1, 0), (1, 1, 1)],
    "up": [(0, 1, 1), (1, 1, 1), (1, 1, 0), (0, 1, 0)],
    "down": [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)],
}


def mat_translate(x, y, z):
    m = np.eye(4); m[:3, 3] = (x, y, z); return m


def mat_scale(x, y, z):
    return np.diag([x, y, z, 1.0])


def mat_rot(rx, ry, rz):
    def rxm(a):
        c, s = math.cos(a), math.sin(a)
        return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1.0]])

    def rym(a):
        c, s = math.cos(a), math.sin(a)
        return np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1.0]])

    def rzm(a):
        c, s = math.cos(a), math.sin(a)
        return np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.0]])

    return rxm(math.radians(rx)) @ rym(math.radians(ry)) @ rzm(math.radians(rz))


def pose_at(anim, frame):
    """Per element (rot, off, stretch) at a frame, interpolated between keyframes."""
    if anim is None:
        return {}
    kfs = sorted(anim["keyframes"], key=lambda k: k["frame"])
    n = anim["quantityframes"]
    loop = anim.get("onAnimationEnd", "Repeat") == "Repeat"
    frame = frame % n if loop else min(frame, n - 1)
    prev = max((k for k in kfs if k["frame"] <= frame), key=lambda k: k["frame"], default=kfs[-1] if loop else kfs[0])
    nxt = min((k for k in kfs if k["frame"] > frame), key=lambda k: k["frame"], default=None)
    if nxt is None:
        nxt = kfs[0] if loop else prev
        span = (n - prev["frame"] + nxt["frame"]) if loop else 1
    else:
        span = nxt["frame"] - prev["frame"]
    t = ((frame - prev["frame"]) % n) / span if span else 0
    out = {}
    for name, a in prev["elements"].items():
        b = nxt["elements"].get(name, a)
        g = lambda k, d=0.0: a.get(k, d) + (b.get(k, d) - a.get(k, d)) * t
        out[name] = ((g("rotationX"), g("rotationY"), g("rotationZ")), (g("offsetX"), g("offsetY"), g("offsetZ")),
                     (g("stretchX", 1), g("stretchY", 1), g("stretchZ", 1)))
    return out


def quads(shape, tex, pose):
    tw, th = shape["textureWidth"], shape["textureHeight"]
    # A shape may give a texture code its own size, which the game uses over textureWidth/Height for faces using it
    sizes = shape.get("textureSizes") or {}
    out = []

    def walk(el, parent):
        origin = [v / 16 for v in el.get("rotationOrigin", [0, 0, 0])]
        (ax, ay, az), (ox, oy, oz), (sx, sy, sz) = pose.get(el["name"], ((0, 0, 0), (0, 0, 0), (1, 1, 1)))
        frm, to = el["from"], el["to"]
        m = parent @ mat_translate(*origin) @ mat_rot(el.get("rotationX", 0) + ax, el.get("rotationY", 0) + ay, el.get("rotationZ", 0) + az) \
            @ mat_scale(sx, sy, sz) @ mat_translate(frm[0] / 16 + ox / 16 - origin[0], frm[1] / 16 + oy / 16 - origin[1], frm[2] / 16 + oz / 16 - origin[2])
        size = [(to[i] - frm[i]) / 16 for i in range(3)]
        for face, f in (el.get("faces") or {}).items():
            if not f or f.get("enabled") is False:
                continue
            pts = []
            for c in FACE_CORNERS[face]:
                p = m @ np.array([c[0] * size[0], c[1] * size[1], c[2] * size[2], 1.0])
                pts.append(p[:3])
            u1, v1, u2, v2 = f["uv"]
            fw, fh = sizes.get(f.get("texture", "").lstrip("#"), (tw, th))
            out.append((pts, (u1 / fw * tex.width, v1 / fh * tex.height, u2 / fw * tex.width, v2 / fh * tex.height), f.get("glow", 0)))
        for ch in el.get("children") or []:
            walk(ch, m)

    for el in shape["elements"]:
        walk(el, np.eye(4))
    return out


def render(shape, tex, pose, yaw, pitch, scale, size, yoff=0):
    W, H = size
    img = Image.new("RGB", (W, H), (58, 58, 66))
    d = ImageDraw.Draw(img)
    cy, sy, cp, sp = math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    light = np.array([0.4, 0.8, 0.45]); light /= np.linalg.norm(light)
    px = tex.load()
    polys = []
    for pts, (u1, v1, u2, v2), glow in quads(shape, tex, pose):
        p = [np.array(q) - np.array([0.5, 0, 0.5]) for q in pts]
        normal = np.cross(p[1] - p[0], p[3] - p[0])
        nl = np.linalg.norm(normal)
        normal = normal / nl if nl > 1e-9 else normal
        k = 0.45 + 0.55 * max(0.0, float(normal @ light))
        if glow:
            k = max(k, 0.5 + glow / 255 * 0.5)
        nu = max(2, min(24, int(round(abs(u2 - u1)))))
        nv = max(2, min(24, int(round(abs(v2 - v1)))))
        for i in range(nu):
            for j in range(nv):
                def at(a, b):
                    return p[0] + (p[1] - p[0]) * a + (p[3] - p[0]) * b
                corners = [at(i / nu, j / nv), at((i + 1) / nu, j / nv), at((i + 1) / nu, (j + 1) / nv), at(i / nu, (j + 1) / nv)]
                uu = u1 + (u2 - u1) * (i + 0.5) / nu
                vv = v2 + (v1 - v2) * (j + 0.5) / nv
                c = px[min(tex.width - 1, max(0, int(uu))), min(tex.height - 1, max(0, int(vv)))]
                if len(c) == 4 and c[3] < 10:
                    continue
                proj, depth = [], 0
                for q in corners:
                    x, y, z = q
                    x, z = x * cy - z * sy, x * sy + z * cy
                    y, z = y * cp - z * sp, y * sp + z * cp
                    proj.append((W / 2 + x * scale, H - 12 - yoff - y * scale))
                    depth += z
                polys.append((depth / 4, proj, tuple(int(v * k) for v in c[:3])))
    for depth, proj, col in sorted(polys, key=lambda t: -t[0]):
        d.polygon(proj, fill=col)
    return img


VIEWS = {"side": (0, 0), "front": (90, 0), "34": (-40, 20), "back": (-90, 0), "top": (0, 70)}


def main():
    shape = json.load(open(sys.argv[1], encoding="utf-8-sig"))
    tex = Image.open(sys.argv[2]).convert("RGBA")
    out = sys.argv[3]
    opts = dict(a.split("=", 1) for a in sys.argv[4:])
    anims = {a["code"]: a for a in shape.get("animations", [])}
    names = opts.get("anims", ",".join(["rest"] + list(anims)[:4])).split(",")
    frames = int(opts.get("frames", 4))
    scale = float(opts.get("scale", 60))
    views = opts.get("views", "side,34").split(",")
    cell = (int(opts.get("cell", 220)), int(opts.get("cellh", 220)))
    sheet = Image.new("RGB", (cell[0] * max(frames, len(views)), cell[1] * len(names)), (30, 30, 34))
    d = ImageDraw.Draw(sheet)
    for row, name in enumerate(names):
        anim = anims.get(name)
        if anim is None:
            cols = [(views[i % len(views)], 0) for i in range(len(views))]
        elif "frame" in opts:
            cols = [(view, int(opts["frame"])) for view in views]       # one frame, every view
        else:
            cols = [(views[0], int(anim["quantityframes"] * c / frames)) for c in range(frames)]
        for col, (view, frame) in enumerate(cols):
            yaw, pitch = VIEWS[view]
            img = render(shape, tex, pose_at(anim, frame), yaw, pitch, scale, cell, int(opts.get("yoff", 0)))
            sheet.paste(img, (col * cell[0], row * cell[1]))
            d.text((col * cell[0] + 4, row * cell[1] + 4), f"{name} {view} f{frame}", fill=(255, 255, 255))
    sheet.save(out)


if __name__ == "__main__":
    main()
