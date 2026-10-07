"""Overlay on map.png: walkable floor of one level that cannot be reached from the level's floor nearest the middle
is painted magenta (sealed floor is left as it is). Run after `mapgen seed cells at mx mz` + `render.py 1`.
Usage: python reachmap.py <level> [scale]"""
import struct, sys, collections
from PIL import Image
want = int(sys.argv[1]); scale = int(sys.argv[2]) if len(sys.argv) > 2 else 2
d = open('tiles.bin', 'rb').read(); size = struct.unpack_from('<i', d, 0)[0]; n = size // 32; off = 4
walk = bytearray(size * size); sealed = bytearray(size * size)
for mz in range(n):
    for mx in range(n):
        for i in range(1024):
            k, fl, ce, flags, lv, pat, var = d[off:off+7]; off += 7
            x = mx*32 + i % 32; z = mz*32 + i // 32
            # floor without a blocking prop, doorway, arch doorway, water
            ok = lv == want and (k in (2, 4, 6) or (k == 0 and not flags & 1 and not flags & 2 and var in (0, 13, 14, 15, 16, 17, 18, 19, 22)))
            walk[z*size + x] = ok
best = None
for i in range(size*size):
    if walk[i]:
        dx, dz = i % size - size//2, i // size - size//2
        if best is None or dx*dx+dz*dz < best[0]: best = (dx*dx+dz*dz, i)
seen = bytearray(size*size); q = collections.deque([best[1]]); seen[best[1]] = 1
while q:
    i = q.popleft(); x, z = i % size, i // size
    for nx, nz in ((x+1,z),(x-1,z),(x,z+1),(x,z-1)):
        if 0 <= nx < size and 0 <= nz < size:
            j = nz*size + nx
            if walk[j] and not seen[j]: seen[j] = 1; q.append(j)
img = Image.open('map.png').convert('RGB'); px = img.load(); lost = 0
for i in range(size*size):
    if walk[i] and not seen[i]:
        px[i % size, i // size] = (255, 0, 255); lost += 1
img.resize((size*scale, size*scale), Image.NEAREST).save('reach.png')
print(f"{lost} unreachable tiles of level {want}")
