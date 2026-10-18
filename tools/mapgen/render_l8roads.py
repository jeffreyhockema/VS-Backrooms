"""Renders l8map.bin (from `mapgen <seed> <cells> l8roads [angle]`) to a PNG.

    python render_l8roads.py [l8map.bin] [out.png] [--scale S] [--crop x,z,w,h]

Level 8's rock is dark brown, the road pale gravel, camp clearings orange with their furniture darker, lamps
yellow, M.E.G. markers cyan, vents and seeps blue, rich deposits magenta, ways through the walls between levels
red; other levels are grey (their walls darker) and Level 7's sea dark blue. --scale shrinks (S < 1, keeping the
road visible: a block of road anywhere in a pixel paints it) or enlarges (S > 1, nearest neighbour); --crop takes a
window in map blocks first.
"""
import struct
import sys

from PIL import Image

COLOURS = {
    0: (120, 120, 120), 1: (75, 75, 75), 2: (46, 34, 26), 3: (225, 210, 170), 4: (235, 140, 40), 5: (255, 240, 60),
    6: (60, 220, 230), 7: (60, 110, 255), 8: (230, 30, 30), 9: (210, 40, 200), 10: (170, 90, 20), 11: (25, 45, 90),
}
# Which code wins when a shrunk pixel covers several (the rarer, smaller things first)
PRIORITY = [8, 5, 6, 4, 10, 3, 7, 9, 2, 11, 0, 1]


def main():
    args = [a for a in sys.argv[1:]]
    scale, crop = 1.0, None
    if "--scale" in args:
        i = args.index("--scale"); scale = float(args[i + 1]); del args[i:i + 2]
    if "--crop" in args:
        i = args.index("--crop"); crop = [int(v) for v in args[i + 1].split(",")]; del args[i:i + 2]
    src = args[0] if args else "l8map.bin"
    out = args[1] if len(args) > 1 else "l8map.png"
    with open(src, "rb") as f:
        size = struct.unpack("<i", f.read(4))[0]
        data = f.read()
    x0, z0, w, h = crop if crop else (0, 0, size, size)
    if scale >= 1:
        img = Image.new("RGB", (w, h))
        px = img.load()
        for z in range(h):
            row = (z0 + z) * size + x0
            for x in range(w):
                px[x, z] = COLOURS.get(data[row + x], (255, 0, 255))
        if scale > 1:
            img = img.resize((int(w * scale), int(h * scale)), Image.NEAREST)
    else:
        step = int(round(1 / scale))
        rank = {c: i for i, c in enumerate(PRIORITY)}
        W, H = w // step, h // step
        img = Image.new("RGB", (W, H))
        px = img.load()
        for Z in range(H):
            for X in range(W):
                best = None
                for dz in range(step):
                    row = (z0 + Z * step + dz) * size + x0 + X * step
                    for c in data[row:row + step]:
                        if best is None or rank.get(c, 99) < rank.get(best, 99):
                            best = c
                px[X, Z] = COLOURS.get(best, (255, 0, 255))
    img.save(out)
    print(f"wrote {out} ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    main()
