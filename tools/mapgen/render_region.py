"""Renders region.bin (from `mapgen <seed> <cells> regionmap <37|94> [dx dz]`) to region.png.

Level 37: tile walls pale grey, slits yellow, water teal (darker the deeper), dry decks white, the Reservoir red,
doors cyan, tunnel mouths black, office carpet grey-blue. Floor more than 14 steps from any slit is shaded dark.
Level 94: ground green by height (stripes light and dark), roads grey, paths tan, houses red (roof), the mountain
pale blue, the castle white and pink, props as dots.
"""
import struct
import sys
from collections import deque

from PIL import Image

FIELDS = 12


def load(path="region.bin"):
    with open(path, "rb") as f:
        size, level = struct.unpack("<ii", f.read(8))
        data = f.read()
    tiles = [data[i * FIELDS:(i + 1) * FIELDS] for i in range(size * size)]
    return size, level, tiles


def main():
    size, level, tiles = load()
    scale = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    img = Image.new("RGB", (size, size))
    px = img.load()
    if level == 12:
        # kind floor pattern variant depth height zone under roof pier stair level
        lit = [False] * (size * size)
        q = deque()
        steps = {0: (0, -1), 1: (0, 1), 2: (1, 0), 3: (-1, 0)}  # ArchPier: West East North South -> fix below
        pier_step = {0: (-1, 0), 1: (1, 0), 2: (0, -1), 3: (0, 1)}
        dist = [99] * (size * size)
        for i, t in enumerate(tiles):
            kind, var, pier = t[0], t[3], t[9]
            if kind == 1 and var in (1, 3):
                dx, dz = pier_step[pier]
                x, z = i % size + dx, i // size + dz
                if 0 <= x < size and 0 <= z < size and tiles[z * size + x][0] == 0:
                    dist[z * size + x] = 0
                    q.append(z * size + x)
        while q:
            i = q.popleft()
            if dist[i] >= 14:
                continue
            x, z = i % size, i // size
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, nz = x + dx, z + dz
                if 0 <= nx < size and 0 <= nz < size:
                    j = nz * size + nx
                    if tiles[j][0] == 0 and dist[j] > dist[i] + 1:
                        dist[j] = dist[i] + 1
                        q.append(j)
        for i, t in enumerate(tiles):
            kind, floor, pattern, var, depth, height, zone, under, roof, pier, stair, lv = t
            x, z = i % size, i // size
            if lv != 12:
                c = (40, 60, 30)
            elif kind == 7:
                c = (0, 220, 230)
            elif kind == 1:
                c = (250, 220, 90) if var == 1 else (255, 250, 200) if var == 3 else (20, 20, 20) if pattern == 56 else (200, 200, 230) if pattern == 10 else \
                    (150, 150, 145) if zone == 0 else (90, 40, 40)
                if var == 2:
                    c = (170, 175, 185)
            else:
                if floor == 11:
                    c = (110, 115, 140)
                elif under == 20:
                    c = (0, 0, 0)
                elif zone == 1:
                    c = (max(60, 170 - depth * 12), 20, 25)
                elif depth == 0:
                    c = (235, 235, 228)
                else:
                    k = min(depth, 22)
                    c = (max(10, 90 - k * 6), max(40, 200 - k * 8), max(50, 190 - k * 6))
                if dist[i] == 99 and zone == 0 and floor != 11 and under != 20:
                    c = tuple(int(v * 0.45) for v in c)
                if var:
                    c = {231: (200, 200, 210), 232: (255, 255, 255), 233: (255, 120, 180), 234: (255, 40, 40), 134: (140, 90, 40), 130: (230, 220, 200)}.get(var, c)
                if under == 22:
                    c = (5, 10, 30)
            px[x, z] = c
    else:
        for i, t in enumerate(tiles):
            kind, floor, pattern, var, depth, height, zone, under, roof, pier, stair, lv = t
            x, z = i % size, i // size
            g = min(height, 60)
            if lv != 13:
                c = (40, 40, 40)
            elif kind == 1 and pattern == 57:
                c = (60, 60, 60)
            elif zone == 2:
                c = (170 + g, 200 + g // 2, 230)
            elif zone in (3, 4):
                if kind == 1:
                    c = (250, 250, 250) if pattern == 59 else (240, 160, 200)
                elif kind == 7:
                    c = (255, 0, 255)
                else:
                    c = (255, 255, 150) if zone == 4 else (120, 140, 230) if floor == 93 else (220, 80, 80) if floor == 94 else (230, 210, 90)
                if var:
                    c = (255, 120, 0)
            elif roof:
                c = (180, 60, 50) if kind != 0 else (200, 90, 70)
            elif kind == 1:
                c = (230, 225, 200)
            elif kind == 7:
                c = (0, 200, 255) if under == 27 else (0, 60, 255) if under == 26 else (120, 80, 40)
            elif kind == 8:
                c = (255, 255, 255)
            elif floor == 91:
                c = (95, 95, 100)
            elif floor == 92:
                c = (200, 200, 195)
            elif floor in (89, 90):
                c = (205, 175, 120)
            else:
                base = 150 + g * 6 if floor == 86 else 130 + g * 6
                c = (40 + g * 3, min(255, base), 40)
            if var and lv == 13 and zone == 0:
                c = {163: (255, 0, 0), 241: (255, 220, 0), 237: (250, 250, 250), 238: (0, 255, 255), 236: (255, 0, 255),
                     239: (255, 255, 255), 240: (30, 30, 120), 245: (140, 90, 40), 246: (90, 40, 10), 160: (20, 90, 20)}.get(var, (255, 160, 60))
            if stair and zone == 0:
                c = (170, 130, 80)
            px[x, z] = c
    if scale != 1:
        img = img.resize((size * scale, size * scale), Image.NEAREST)
    img.save("region.png")
    print("region.png", img.size)


if __name__ == "__main__":
    main()
