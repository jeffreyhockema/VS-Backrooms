"""Renders l36map.bin (from `mapgen <seed> <cells> 36map [w h]`) to l36map.png: Level 36's zones from above.

Walls dark grey (window walls pale blue, gate doors orange, static white), floors by zone, blackouts darkened, props as
dark dots, hanging signs and screens yellow, supply boxes red, lit panels white. Not the level's: black.

    python tools/mapgen/render_36.py [l36map.bin] [scale]
"""
import struct
import sys

from PIL import Image

ZONE = {
    3: (196, 180, 150), 4: (150, 130, 100), 5: (210, 210, 220), 6: (150, 80, 200), 7: (160, 170, 180), 8: (235, 235, 230),
    9: (250, 250, 250), 10: (200, 210, 230), 11: (90, 150, 150), 12: (120, 120, 140), 13: (60, 90, 200), 14: (230, 240, 250),
    15: (225, 215, 200), 16: (200, 170, 140), 17: (230, 200, 150), 18: (170, 60, 60), 19: (255, 230, 120), 20: (110, 105, 95),
    21: (80, 80, 90),
}


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "l36map.bin"
    scale = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    with open(path, "rb") as f:
        w, h = struct.unpack("<ii", f.read(8))
        data = f.read()
    img = Image.new("RGB", (w, h))
    px = img.load()
    for i in range(w * h):
        zone, kind, detail, flags = data[i * 4:i * 4 + 4]
        x, z = i % w, i // w
        mat = detail & 15
        if zone == 255:
            c = (0, 0, 0)
        elif kind != 0:
            c = (255, 255, 255) if detail & 32 else (150, 200, 240) if mat == 7 else (240, 140, 40) if mat == 8 else (70, 70, 75)
        else:
            c = ZONE.get(zone, (255, 0, 255))
            if mat in (9, 10):
                c = (40, 40, 40) if mat == 9 else (90, 90, 90)
            if mat in (11, 12):
                c = (120, 120, 60)
            if detail & 16:
                c = tuple(v // 3 for v in c)
            if detail & 32:
                c = (255, 255, 255)
            if flags & 1:
                c = tuple(v * 2 // 3 for v in c)
            if flags & 2:
                c = (240, 210, 0)
            if flags & 8:
                c = (255, 255, 200)
            if flags & 4:
                c = (230, 0, 0)
        px[x, z] = c
    if scale != 1:
        img = img.resize((w * scale, h * scale), Image.NEAREST)
    img.save("l36map.png")
    print("wrote l36map.png", img.size)


if __name__ == "__main__":
    main()
