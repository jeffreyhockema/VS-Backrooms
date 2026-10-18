"""Draws l4plan.bin (mapgen <seed> <cells> l4plan) as a plan of Level 4's floor with its ceiling over it.

    python render_l4plan.py l4plan.bin out.png [scale] [x0 z0 w h]

Floor pale grey (tan under a prop), walls dark, doors brown, lone columns black; ceiling: troffers yellow (dead ones
olive, flickering orange), diffusers blue outlines, water stains brown, missing tiles purple, sprinkler heads red dots
where they hang (the middle of the block's south half); stairs hatched; a whiteboard is a strip on the face it hangs on
(one block teal, a two-block board's halves cyan). Other levels are drawn faded; cell edges are pink lines. North is
up, x east.
"""
import struct
import sys

from PIL import Image, ImageDraw

WALLISH = (1, 2, 3, 4, 7)
LIGHT_ON, LIGHT_LIT, LIGHT_OFF, LIGHT_FLICKER = 1, 2, 3, 5
VENT, SPRINKLER, STAIN = 10, 11, 12
WB, WBL, WBR = 82, 97, 98
WEST, EAST, NORTH, SOUTH = 0, 1, 2, 3  # ArchPier


def main():
    src, out = sys.argv[1], sys.argv[2]
    scale = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    d = open(src, "rb").read()
    size = struct.unpack_from("<i", d, 0)[0]
    rec = 7
    tiles = [d[4 + i * rec:4 + (i + 1) * rec] for i in range(size * size)]
    x0, z0, w, h = (int(v) for v in sys.argv[4:8]) if len(sys.argv) > 7 else (0, 0, size, size)
    img = Image.new("RGB", (w * scale, h * scale), (255, 255, 255))
    dr = ImageDraw.Draw(img)

    def at(x, z):
        return tiles[z * size + x] if 0 <= x < size and 0 <= z < size else None

    for z in range(z0, z0 + h):
        for x in range(x0, x0 + w):
            kind, ceil, over, var, flags, lvl, pier = at(x, z)
            px, pz = (x - x0) * scale, (z - z0) * scale
            box = [px, pz, px + scale - 1, pz + scale - 1]
            fade = lvl != 4
            if kind in WALLISH:
                lone = kind == 1 and all(at(x + dx, z + dz) is not None and at(x + dx, z + dz)[0] not in WALLISH
                                         for dx in (-1, 0, 1) for dz in (-1, 0, 1) if dx or dz)
                c = (10, 10, 10) if lone else (150, 110, 70) if kind in (2, 4, 7) else (90, 90, 96)
                dr.rectangle(box, fill=fade_c(c, fade))
                if var in (WB, WBL, WBR) and lvl == 4:
                    c = (40, 150, 150) if var == WB else (0, 230, 255)
                    t = max(2, scale // 4)
                    strip = {NORTH: [px, pz, px + scale - 1, pz + t - 1], SOUTH: [px, pz + scale - t, px + scale - 1, pz + scale - 1],
                             WEST: [px, pz, px + t - 1, pz + scale - 1], EAST: [px + scale - t, pz, px + scale - 1, pz + scale - 1]}[pier]
                    dr.rectangle(strip, fill=c)
                continue
            dr.rectangle(box, fill=fade_c((198, 186, 160) if var else (222, 222, 218), fade))
            if flags & 2:
                for k in range(0, scale, 3):
                    dr.line([px + k, pz, px, pz + k], fill=fade_c((160, 160, 160), fade))
                continue
            if flags & 1:
                dr.rectangle([px + 1, pz + 1, px + scale - 2, pz + scale - 2], fill=fade_c((120, 60, 150), fade))
            elif ceil in (LIGHT_ON, LIGHT_LIT):
                dr.rectangle([px + 1, pz + 1, px + scale - 2, pz + scale - 2], fill=fade_c((250, 215, 40), fade))
            elif ceil == LIGHT_OFF:
                dr.rectangle([px + 1, pz + 1, px + scale - 2, pz + scale - 2], fill=fade_c((150, 145, 90), fade))
            elif ceil == LIGHT_FLICKER:
                dr.rectangle([px + 1, pz + 1, px + scale - 2, pz + scale - 2], fill=fade_c((240, 140, 30), fade))
            elif over == VENT:
                dr.rectangle([px + 2, pz + 2, px + scale - 3, pz + scale - 3], outline=fade_c((40, 90, 220), fade))
            elif over == STAIN:
                dr.rectangle([px + 1, pz + 1, px + scale - 2, pz + scale - 2], fill=fade_c((190, 165, 120), fade))
            elif over == SPRINKLER:
                cx, cz, r = px + scale * 0.5, pz + scale * 0.75, max(1.5, scale * 0.22)
                dr.ellipse([cx - r, cz - r, cx + r, cz + r], fill=fade_c((220, 20, 20), fade))
    # Cell lines
    for g in range(0, max(w, h) + 1):
        for k, (a, b) in enumerate(((x0 + g, 0), (z0 + g, 1))):
            if a % 32 == 0:
                if b == 0 and g <= w:
                    dr.line([g * scale, 0, g * scale, h * scale], fill=(255, 120, 200))
                if b == 1 and g <= h:
                    dr.line([0, g * scale, w * scale, g * scale], fill=(255, 120, 200))
    img.save(out)
    print(f"{out}: {w}x{h} tiles")


def fade_c(c, fade):
    return tuple(int(v * 0.35 + 255 * 0.65) for v in c) if fade else c


if __name__ == "__main__":
    main()
