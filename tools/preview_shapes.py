"""Renders isometric previews of block shapes (seen from the north-west, above), to judge models without the client.

    python tools/preview_shapes.py out.png shapes/block/detail/desk.json ...   (globs allowed, relative to assets/backrooms)
        [--flat] [--size 256] [--cols 8] [--yaw 225] [--pitch 30] [--zoom 1] [--centre x,y,z] [--hide Prefix,Prefix]

--yaw/--pitch turn the camera (yaw is atan2(z, x) in degrees from the model's centre to the camera: 225 north-west, the
default; 270 from the north, 90 from the south, 180 west, 0 east), --zoom scales the frame, --centre (shape units) says
where the frame is centred, and --hide leaves out the elements whose names start with one of the prefixes (a roof, say, to
look into a car from above). A car is 32 by 64 units: --centre 16,8,32 --zoom 0.6.

By default each face shows its real texture: the face's UV rectangle (from the shape JSON, or worked out from the
element's size where the face has none, as the game does) is cut out of the texture and mapped onto the face with
nearest-neighbour sampling, then darkened by the face's facing. Element rotations and child elements are applied.
First version, known gaps: a face's own "rotation" (turning its texture by 90/180/270) is ignored, so a rotated face
shows its texture unturned; textures come from the shape's own "textures" (a blocktype that overrides them is not
read). Faces are drawn with a per-pixel depth test, so thin plates in front of big faces and parts that pass through
each other show as the game would draw them.

--flat is the old rough mode: each face filled with the average colour of its texture.
"""
import glob
import json
import math
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets")
GAME = os.environ.get("VINTAGE_STORY", os.path.join(os.environ.get("APPDATA", ""), "Vintagestory"))
_colours = {}
_images = {}


def tex_file(path):
    domain, rel = path.split(":") if ":" in path else ("backrooms", path)
    if domain == "game":
        for sub in ("survival", "game", "creative"):
            f = os.path.join(GAME, "assets", sub, "textures", rel + ".png")
            if os.path.exists(f):
                return f
    return os.path.join(ASSETS, domain, "textures", rel + ".png")


def tex_image(path):
    if path not in _images:
        try:
            _images[path] = Image.open(tex_file(path)).convert("RGBA")
        except OSError:
            _images[path] = None
    return _images[path]


def tex_colour(path):
    if path not in _colours:
        im = tex_image(path)
        _colours[path] = im.resize((1, 1), Image.BOX).getpixel((0, 0))[:3] if im is not None else (255, 0, 255)
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


# Corners of each face in the unit cube, in texture order: top-left, top-right, bottom-right, bottom-left, as the
# face is seen from outside the block (north faces have east on the left; up faces run +x along u and +z along v)
FACES = {"north": ((1, 1, 0), (0, 1, 0), (0, 0, 0), (1, 0, 0)), "south": ((0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 1)),
         "west": ((0, 1, 0), (0, 1, 1), (0, 0, 1), (0, 0, 0)), "east": ((1, 1, 1), (1, 1, 0), (1, 0, 0), (1, 0, 1)),
         "up": ((0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)), "down": ((0, 0, 1), (1, 0, 1), (1, 0, 0), (0, 0, 0))}
NORMALS = {"north": (0, 0, -1), "south": (0, 0, 1), "west": (-1, 0, 0), "east": (1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}
VIEW = (-math.cos(math.radians(30)) / math.sqrt(2), math.sin(math.radians(30)), -math.cos(math.radians(30)) / math.sqrt(2))
SHADE = {"north": 0.85, "south": 0.5, "west": 0.68, "east": 0.6, "up": 1.0, "down": 0.4}


def auto_uv(face, f0, t0):
    """The UV the game gives a face that has none: the element's extent on that face, in shape units."""
    x0, y0, z0 = f0
    x1, y1, z1 = t0
    return {"north": (16 - x1, 16 - y1, 16 - x0, 16 - y0), "south": (x0, 16 - y1, x1, 16 - y0),
            "west": (z0, 16 - y1, z1, 16 - y0), "east": (16 - z1, 16 - y1, 16 - z0, 16 - y0),
            "up": (x0, z0, x1, z1), "down": (x0, 16 - z1, x1, 16 - z0)}[face]


# The camera, set by --yaw/--pitch/--zoom/--centre/--hide. yaw: the horizontal direction the camera sits in from the
# model's centre, atan2(z, x) in degrees (225 is north-west, the default view; 270 is north of the model, looking south;
# 90 is south of it, looking north; 180 west; 0 east); pitch: degrees above the horizon; zoom: scale on the default
# 44-unit frame; centre: the point in shape units the frame is centred on; hide: element-name prefixes left out.
CAM = {"yaw": 225.0, "pitch": 30.0, "zoom": 1.0, "centre": (8.0, 0.0, 8.0), "hide": ()}


def view_vector():
    b, a = math.radians(CAM["pitch"]), math.radians(CAM["yaw"])
    return (math.cos(a) * math.cos(b), math.sin(b), math.sin(a) * math.cos(b))


def project(p, scale, cx, cy):
    # Default: camera to the north-west, above, looking south-east and down 30 degrees: fronts (north faces) and west
    # sides show
    x, y, z = p[0] - CAM["centre"][0], p[1] - CAM["centre"][1], p[2] - CAM["centre"][2]
    b, a = math.radians(CAM["pitch"]), math.radians(CAM["yaw"])
    hx, hz = math.cos(a), math.sin(a)
    h = -(hx * x + hz * z)
    sx = hz * x - hx * z
    sy = y * math.cos(b) + h * math.sin(b)
    depth = y * math.sin(b) - h * math.cos(b)
    return cx + sx * scale, cy - sy * scale, depth


def walk(elements, chain=()):
    """Every element with the transforms of its parents (children are placed relative to their parent's from)."""
    for el in elements:
        yield el, chain
        if el.get("children"):
            yield from walk(el["children"], chain + (el,))


def place(p, el, chain):
    origin = el.get("rotationOrigin", [8, 8, 8])
    p = rotate(p, origin, el.get("rotationX", 0), el.get("rotationY", 0), el.get("rotationZ", 0))
    for parent in reversed(chain):
        f = parent["from"]
        p = (p[0] + f[0], p[1] + f[1], p[2] + f[2])
        o = parent.get("rotationOrigin", [8, 8, 8])
        p = rotate(p, o, parent.get("rotationX", 0), parent.get("rotationY", 0), parent.get("rotationZ", 0))
    return p


def orient(v, el, chain):
    """A direction turned by the element's rotation and its parents'."""
    for e in (el,) + tuple(reversed(chain)):
        v = rotate(v, (0, 0, 0), e.get("rotationX", 0), e.get("rotationY", 0), e.get("rotationZ", 0))
    return v


def texture_patch(path, uv, tw, th, sizes):
    im = tex_image(path)
    if im is None:
        return None
    w, h = sizes.get(path, (tw, th))
    kx, ky = im.width / w, im.height / h
    u0, v0, u1, v1 = uv
    x0, x1 = sorted((u0 * kx, u1 * kx))
    y0, y1 = sorted((v0 * ky, v1 * ky))
    box = (int(math.floor(x0)), int(math.floor(y0)), max(int(math.floor(x0)) + 1, int(math.ceil(x1))),
           max(int(math.floor(y0)) + 1, int(math.ceil(y1))))
    patch = Image.new("RGBA", (box[2] - box[0], box[3] - box[1]))
    # wrap round the texture, as UVs past its edge do in the game
    for j in range(patch.height):
        for i in range(patch.width):
            patch.putpixel((i, j), im.getpixel(((box[0] + i) % im.width, (box[1] + j) % im.height)))
    if u0 > u1:
        patch = patch.transpose(Image.FLIP_LEFT_RIGHT)
    if v0 > v1:
        patch = patch.transpose(Image.FLIP_TOP_BOTTOM)
    return patch


def _zpaste(out, zbuf, rgb, mask, x0, y0, z0, za, zb):
    """Pastes rgb where mask is set and the face (depth z0 + za*(x-x0) + zb*(y-y0)) is nearer than what is there."""
    box = mask.getbbox()
    if not box:
        return
    m, c = mask.load(), rgb.load()
    for y in range(box[1], box[3]):
        row = zbuf[y]
        for x in range(box[0], box[2]):
            if m[x, y]:
                z = z0 + za * (x + 0.5 - x0) + zb * (y + 0.5 - y0)
                if z >= row[x] - 1e-3:
                    row[x] = z
                    out[x, y] = c[x, y] + (255,)


def render(shape_path, size=200, flat=False):
    data = json.load(open(shape_path, encoding="utf-8"))
    tex = data.get("textures", {})
    tw, th = data.get("textureWidth", 16), data.get("textureHeight", 16)
    sizes = {tex.get(k, k): tuple(v) for k, v in data.get("textureSizes", {}).items()}
    scale = size / 44 * CAM["zoom"]
    VIEW = view_vector()
    cy0 = size * 0.78 if CAM["centre"][1] == 0 else size / 2
    faces = []
    for el, chain in walk(data["elements"]):
        if el.get("name", "").startswith(CAM["hide"]):
            continue
        f0, t0 = el["from"], el["to"]
        for face, info in el.get("faces", {}).items():
            if info.get("enabled") is False or face not in FACES or "texture" not in info:
                continue
            n = orient(NORMALS[face], el, chain)
            if n[0] * VIEW[0] + n[1] * VIEW[1] + n[2] * VIEW[2] <= 0.01:
                continue  # facing away from the camera
            corners = [place(tuple(f0[i] + (t0[i] - f0[i]) * c[i] for i in range(3)), el, chain) for c in FACES[face]]
            pr = [project(c, scale, size / 2, cy0) for c in corners]
            depth = sum(p[2] for p in pr) / 4
            path = tex.get(info["texture"].lstrip("#"), "?")
            k = SHADE[face] if not info.get("glow") else 1.1
            uv = info.get("uv") or auto_uv(face, f0, t0)
            faces.append((depth, [(p[0], p[1]) for p in pr], path, k, uv, [p[2] for p in pr]))
    img = Image.new("RGBA", (size, size), (40, 44, 48, 255))
    d = ImageDraw.Draw(img)
    zbuf = [[-1e9] * size for _ in range(size)]
    out = img.load()
    for _, poly, path, k, uv, zs in sorted(faces, key=lambda t: t[0]):
        (x0, y0), (x1, y1), _, (x3, y3) = poly
        ax, ay, bx, by = x1 - x0, y1 - y0, x3 - x0, y3 - y0
        det = ax * by - bx * ay
        if abs(det) < 1e-6:
            continue
        # the face's depth as a plane over the screen, for the depth test (nearer = larger)
        za = ((zs[1] - zs[0]) * by - (zs[3] - zs[0]) * ay) / det
        zb = ((zs[3] - zs[0]) * ax - (zs[1] - zs[0]) * bx) / det
        patch = None if flat else texture_patch(path, uv, tw, th, sizes)
        if patch is None:
            col = tex_colour(path)
            rgb = Image.new("RGB", (size, size), tuple(min(255, int(v * k)) for v in col))
            mask = Image.new("L", (size, size), 0)
            ImageDraw.Draw(mask).polygon(poly, fill=255)
            _zpaste(out, zbuf, rgb, mask, x0, y0, zs[0], za, zb)
            continue
        # affine map from the screen back into the patch: TL, TR, BL corners of the face
        pw, ph = patch.size
        a, b = pw * by / det, -pw * bx / det
        dd, e = -ph * ay / det, ph * ax / det
        c, f = -(a * x0 + b * y0), -(dd * x0 + e * y0)
        warped = patch.transform((size, size), Image.AFFINE, (a, b, c, dd, e, f), resample=Image.NEAREST)
        rgb = warped.convert("RGB").point(lambda v: min(255, int(v * k)))
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).polygon(poly, fill=255)
        alpha = warped.getchannel("A").point(lambda v: 255 if v >= 128 else 0)  # alpha-tested, as the game draws cutouts
        mask = Image.composite(alpha, mask, mask)
        _zpaste(out, zbuf, rgb, mask, x0, y0, zs[0], za, zb)
    # ground grid of the block's own footprint
    g = [project(p, scale, size / 2, cy0) for p in ((0, 0, 0), (16, 0, 0), (16, 0, 16), (0, 0, 16))]
    d.polygon([(p[0], p[1]) for p in g], outline=(120, 200, 120, 255))
    return img


if __name__ == "__main__":
    args = sys.argv[1:]
    flat = "--flat" in args
    if flat:
        args.remove("--flat")
    opts = {"--size": 200 if flat else 256, "--cols": 8}
    for o in list(opts):
        if o in args:
            i = args.index(o)
            opts[o] = int(args[i + 1])
            del args[i:i + 2]
    for o, key in (("--yaw", "yaw"), ("--pitch", "pitch"), ("--zoom", "zoom")):
        if o in args:
            i = args.index(o)
            CAM[key] = float(args[i + 1])
            del args[i:i + 2]
    if "--centre" in args:
        i = args.index("--centre")
        CAM["centre"] = tuple(float(v) for v in args[i + 1].split(","))
        del args[i:i + 2]
    if "--hide" in args:
        i = args.index("--hide")
        CAM["hide"] = tuple(args[i + 1].split(","))
        del args[i:i + 2]
    if len(args) < 2:
        sys.exit(__doc__)
    out = args[0]
    files = []
    for pattern in args[1:]:
        files += sorted(glob.glob(os.path.join(ASSETS, "backrooms", pattern))) or sorted(glob.glob(pattern))
    cols, cell = opts["--cols"], opts["--size"]
    sheet = Image.new("RGBA", (cols * cell, ((len(files) + cols - 1) // cols) * (cell + 14)), (30, 30, 30, 255))
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(files):
        x, y = (i % cols) * cell, (i // cols) * (cell + 14)
        sheet.alpha_composite(render(f, cell, flat), (x, y))
        d.text((x + 3, y + cell), os.path.basename(f)[:-5][:30], fill=(255, 255, 255, 255))
    sheet.save(out)
    print(len(files), "shapes")
