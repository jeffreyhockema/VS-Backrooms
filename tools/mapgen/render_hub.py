"""Renders hubmap.bin (from `mapgen <seed> <cells> hubmap [step]`) to hubmap.png, and a close-up (hubzoom.png).

Solid black, wall faces grey, road dark, studs yellow, sidewalks pale, level doors amber (open ones bright),
service doors blue, dead doors brown, the Tower's ornate doors white, holes red, false walls magenta, tiled ends cyan,
lamps orange (dead ones dark red), stencils white, overheads green.

    python render_hub.py [zoom_cx zoom_cz zoom_size]   (zoom centre in map pixels; default the middle)
"""
import struct
import sys

from PIL import Image

COLOURS = {
    0: (8, 8, 10), 1: (110, 106, 100), 2: (52, 50, 48), 3: (232, 185, 42), 4: (170, 164, 152), 5: (225, 220, 210),
    6: (120, 80, 50), 7: (255, 160, 30), 8: (60, 120, 230), 9: (255, 255, 255), 10: (220, 20, 20), 11: (230, 40, 230),
    12: (40, 230, 230), 13: (240, 240, 236), 14: (255, 140, 0), 15: (110, 20, 20), 16: (255, 255, 255), 17: (255, 255, 0),
    18: (40, 200, 60),
}


def main():
    with open("hubmap.bin", "rb") as f:
        size, x0, z0, step = struct.unpack("<iiii", f.read(16))
        data = f.read(size * size)
    img = Image.new("RGB", (size, size))
    img.putdata([COLOURS.get(b, (255, 0, 255)) for b in data])
    full = img.resize((min(size, 2000), min(size, 2000)), Image.NEAREST if size <= 2000 else Image.BOX)
    full.save("hubmap.png")
    cx = int(sys.argv[1]) if len(sys.argv) > 1 else size // 2
    cz = int(sys.argv[2]) if len(sys.argv) > 2 else size // 2
    zs = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    zoom = img.crop((cx - zs // 2, cz - zs // 2, cx + zs // 2, cz + zs // 2)).resize((zs * 3, zs * 3), Image.NEAREST)
    zoom.save("hubzoom.png")
    print(f"hubmap.png ({size}x{size}, step {step}, from {x0},{z0}); hubzoom.png round {cx},{cz}")


if __name__ == "__main__":
    main()
