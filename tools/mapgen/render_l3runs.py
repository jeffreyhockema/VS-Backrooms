"""Draws Level 3's wall runs from above, from the harness's l3dump.json (mapgen <seed> <cells> l3dump x z r).

    python tools/mapgen/render_l3runs.py l3dump.json out.png [--px 16] [--title "..."]

Walls by material, the wall pipes as an orange band on every face the generator draws them on (as
WorldGenerator.PipeOpen), gauges on them as red dots, cable runs on the walls as a blue band on the face they are on,
panels (grey) and junction boxes (teal) on their faces, the cables on the floor in blue with their end fittings (a
square: a cable box; a triangle: rising into the fitting on the wall), switchgear cabinets in purple with a white edge
on their front, other machines and props as dark squares.
"""
import argparse
import json

from PIL import Image, ImageDraw, ImageFont

# Kinds, props and decorations as numbered in src/Worldgen/Tiles.cs
WALLPIPES, WALLPANEL, WALLFAN = 1, 7, 8
GAUGES, JUNCTIONBOX, WALLCABLES, RISERS, BULKHEAD = 61, 63, 67, 68, 65
SWITCHGEAR, FLOORCABLE = 61, 69  # props (floor tiles)


def load_enums():
    """Reads the TileKind and WallPattern enums from Tiles.cs, so the numbers follow the code."""
    import os
    import re
    src = open(os.path.join(os.path.dirname(__file__), "..", "..", "src", "Worldgen", "Tiles.cs"), encoding="utf-8").read()

    def enum(name):
        m = re.search(r"enum " + name + r"[^{]*\{([^}]*)\}", src)
        body = re.sub(r"//[^\n]*|/\*.*?\*/|///[^\n]*", "", m.group(1), flags=re.S)
        out, n = {}, 0
        for part in body.split(","):
            part = re.sub(r"\[[^\]]*\]", "", part).strip()
            if not part:
                continue
            if "=" in part:
                k, v = (s.strip() for s in part.split("="))
                n = int(v, 0)
            else:
                k = part
            out[k] = n
            n += 1
        return out
    return enum("TileKind"), enum("WallPattern")


DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # north, east, south, west
PIER = {0: 3, 1: 1, 2: 0, 3: 2}  # ArchPier (West, East, North, South) to the index in DIRS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dump")
    ap.add_argument("out")
    ap.add_argument("--px", type=int, default=16)
    ap.add_argument("--title", default="")
    ap.add_argument("--standalone-gauges", action="store_true",
                    help="draw gauges as decorations on a pipe of their own, as the code before layout version 9's runs did")
    a = ap.parse_args()
    kinds, patterns = load_enums()
    K = {v: k for k, v in kinds.items()}
    P = {v: k for k, v in patterns.items()}
    d = json.load(open(a.dump, encoding="utf-8"))
    tiles, n, px = d["tiles"], d["size"], a.px

    def at(x, z):
        if 0 <= x < n and 0 <= z < n:
            return tiles[z][x]
        return None

    def kind(t):
        return K.get(t[0], "?") if t else "?"

    def pipe_open(t):
        return kind(t) in ("Floor", "Doorway", "Pit", "Bars", "Water", "ArchDoor")

    def carries(t):
        return kind(t) == "Wall" and t[5] == 3 and P.get(t[4]) != "Stone" and (t[1] == WALLPIPES or d["version"] >= 9 and not a.standalone_gauges and t[1] == GAUGES)

    head = 40 if a.title else 0
    legend = 54 if n * px >= 760 else 100
    img = Image.new("RGB", (n * px, n * px + head + legend), (250, 250, 248))
    dr = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 13)
        big = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        font = big = ImageFont.load_default()
    if a.title:
        dr.text((8, 10), a.title, fill=(20, 20, 20), font=big)
    wallc = {"GlazedTile": (120, 140, 140), "RedBrick": (140, 90, 75), "Cinder": (128, 126, 120), "Stone": (190, 185, 170)}

    def box(x, z):
        return x * px, z * px + head, (x + 1) * px - 1, (z + 1) * px - 1 + head

    for z in range(n):
        for x in range(n):
            t = tiles[z][x]
            k = kind(t)
            x1, y1, x2, y2 = box(x, z)
            if k == "Wall":
                dr.rectangle((x1, y1, x2, y2), fill=wallc.get(P.get(t[4]), (100, 100, 100)))
            elif k in ("Door", "ArchWindow"):
                dr.rectangle((x1, y1, x2, y2), fill=(70, 60, 50))
            elif k == "Doorway":
                dr.rectangle((x1, y1, x2, y2), fill=(225, 205, 160))
            elif k == "Bars":
                dr.rectangle((x1, y1, x2, y2), fill=(235, 235, 235))
                for i in range(2, px, 4):
                    dr.line((x1 + i, y1, x1 + i, y2), fill=(90, 90, 90))
            else:
                dr.rectangle((x1, y1, x2, y2), fill=(214, 212, 205) if not t[6] else (200, 196, 186), outline=(228, 226, 220))
            if t[5] != 3 and k != "Wall":
                dr.rectangle((x1, y1, x2, y2), fill=(235, 230, 240))
    q = max(2, px // 5)
    for z in range(n):
        for x in range(n):
            t = tiles[z][x]
            k = kind(t)
            x1, y1, x2, y2 = box(x, z)
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            if k == "Floor" and t[1] >= 40:
                v, pier = t[1], PIER[t[2]]
                if v == SWITCHGEAR:
                    dr.rectangle((x1 + 1, y1 + 1, x2 - 1, y2 - 1), fill=(120, 60, 160))
                    fx, fz = DIRS[pier]
                    # the front edge
                    if fx:
                        xe = x2 - 1 if fx > 0 else x1 + 1
                        dr.line((xe, y1 + 2, xe, y2 - 2), fill=(255, 255, 255), width=3)
                    else:
                        ye = y2 - 1 if fz > 0 else y1 + 1
                        dr.line((x1 + 2, ye, x2 - 2, ye), fill=(255, 255, 255), width=3)
                elif v == FLOORCABLE:
                    blue = (40, 90, 220)
                    stack = t[3]
                    if stack == 0:
                        along_x = t[2] == 2  # Pier North: along X
                        if along_x:
                            dr.line((x1, cy, x2, cy), fill=blue, width=3)
                        else:
                            dr.line((cx, y1, cx, y2), fill=blue, width=3)
                    else:
                        fx, fz = DIRS[pier]
                        # from the open side to the wall it ends at
                        ex, ey = cx + fx * px * 0.42, cy + fz * px * 0.42
                        sx, sy = cx - fx * px * 0.5, cy - fz * px * 0.5
                        dr.line((sx, sy, ex, ey), fill=blue, width=3)
                        if stack == 1:
                            dr.rectangle((ex - q, ey - q, ex + q, ey + q), fill=(30, 50, 120))
                        else:
                            dr.polygon([(ex - q, ey + q), (ex + q, ey + q), (ex, ey - q)], fill=(30, 50, 120))
                else:
                    dr.rectangle((x1 + 3, y1 + 3, x2 - 3, y2 - 3), fill=(80, 80, 80))
            if k != "Wall":
                continue
            v = t[1]
            # The faces of this wall that look into the open
            for f, (dx, dz) in enumerate(DIRS):
                o = at(x + dx, z + dz)
                if not pipe_open(o):
                    continue
                # a band along the face, inside the wall block
                if dx == 0:
                    yb = y1 if dz < 0 else y2 - q
                    band = (x1, yb, x2, yb + q)
                else:
                    xb = x1 if dx < 0 else x2 - q
                    band = (xb, y1, xb + q, y2)
                if carries(t):
                    dr.rectangle(band, fill=(240, 140, 20))
                    if v == GAUGES and PIER[t[2]] == f:
                        mx_, my_ = (band[0] + band[2]) / 2, (band[1] + band[3]) / 2
                        dr.ellipse((mx_ - q - 1, my_ - q - 1, mx_ + q + 1, my_ + q + 1), fill=(220, 20, 20))
                elif v == WALLCABLES and PIER[t[2]] == f:
                    dr.rectangle(band, fill=(40, 90, 220))
                elif v == WALLPANEL:
                    mx_, my_ = (band[0] + band[2]) / 2, (band[1] + band[3]) / 2
                    dr.rectangle((mx_ - q, my_ - q, mx_ + q, my_ + q), fill=(225, 225, 225), outline=(40, 40, 40))
                elif v == JUNCTIONBOX and PIER[t[2]] == f:
                    mx_, my_ = (band[0] + band[2]) / 2, (band[1] + band[3]) / 2
                    dr.rectangle((mx_ - q, my_ - q, mx_ + q, my_ + q), fill=(40, 170, 160), outline=(20, 60, 60))
                elif v == GAUGES and PIER[t[2]] == f:
                    # (a gauge on a length of pipe of its own, as in 1-8)
                    dr.rectangle(band, fill=(250, 200, 150))
                    mx_, my_ = (band[0] + band[2]) / 2, (band[1] + band[3]) / 2
                    dr.ellipse((mx_ - q - 1, my_ - q - 1, mx_ + q + 1, my_ + q + 1), fill=(220, 20, 20))
    # Legend
    y0 = n * px + head + 8
    items = [((240, 140, 20), "wall pipes"), ((220, 20, 20), "gauge"), ((40, 90, 220), "cables (wall, floor)"),
             ((225, 225, 225), "panel"), ((40, 170, 160), "junction box"), ((120, 60, 160), "switchgear (white: front)"),
             ((250, 200, 150), "gauge on its own pipe")]
    xx = 8
    for col, label in items:
        dr.rectangle((xx, y0, xx + 14, y0 + 14), fill=col, outline=(40, 40, 40))
        dr.text((xx + 18, y0), label, fill=(20, 20, 20), font=font)
        xx += 26 + int(dr.textlength(label, font=font))
        if xx > n * px - 160:
            xx, y0 = 8, y0 + 20
    img.save(a.out)


if __name__ == "__main__":
    main()
