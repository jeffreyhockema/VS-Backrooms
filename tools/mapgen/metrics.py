"""Layout metrics from tiles.bin: how a level *reads*, in numbers.
wall%      share of tiles that block movement (wall, door, bars, window, pit)
sight      mean length of a straight open run (both axes), i.e. how far you see down a line
sight90    90th percentile of that
dead%      share of open tiles with exactly one open neighbour (dead ends)
frag       wall fragments: mean length of a straight wall segment (short = confetti)
enclosed%  share of open tiles that are inside a "room": 4-neighbour flood region bounded by walls, size < 400
"""
import struct, sys, collections
d = open('tiles.bin', 'rb').read(); size = struct.unpack_from('<i', d, 0)[0]; n = size // 32; off = 4
kind = [[0]*size for _ in range(size)]; lvl = [[0]*size for _ in range(size)]
for mz in range(n):
    for mx in range(n):
        for i in range(1024):
            k, fl, ce, flags, lv, pat, var = d[off:off+7]; off += 7
            x = mx*32 + i % 32; z = mz*32 + i // 32
            kind[z][x] = k; lvl[z][x] = lv
BLOCK = {1, 3, 5, 7, 8}           # wall, archwindow, pit, door, bars
want = int(sys.argv[1]) if len(sys.argv) > 1 else None
def openat(x, z): return 0 <= x < size and 0 <= z < size and kind[z][x] not in BLOCK and (want is None or lvl[z][x] == want)
tiles = [(x, z) for z in range(size) for x in range(size) if want is None or lvl[z][x] == want]
opens = [(x, z) for x, z in tiles if openat(x, z)]
walls = [(x, z) for x, z in tiles if kind[z][x] in BLOCK]
# straight open runs along x and z
runs = []
for axis in (0, 1):
    for a in range(size):
        run = 0
        for b in range(size):
            x, z = (b, a) if axis == 0 else (a, b)
            if openat(x, z): run += 1
            else:
                if run: runs.append(run)
                run = 0
        if run: runs.append(run)
runs.sort()
# per open tile: the longer of its x-run and z-run (what a player standing there can see along)
xr = {}; zr = {}
for axis, store in ((0, xr), (1, zr)):
    for a in range(size):
        b = 0
        while b < size:
            x, z = (b, a) if axis == 0 else (a, b)
            if not openat(x, z): b += 1; continue
            c = b
            while c < size and openat(*((c, a) if axis == 0 else (a, c))): c += 1
            for k in range(b, c): store[((k, a) if axis == 0 else (a, k))] = c - b
            b = c
view = sorted(max(xr.get(t, 1), zr.get(t, 1)) for t in opens)
width = sorted(min(xr.get(t, 1), zr.get(t, 1)) for t in opens)
def wallat(x, z): return 0 <= x < size and 0 <= z < size and kind[z][x] in BLOCK and (want is None or lvl[z][x] == want)
wx = {}; wz = {}
for axis, store in ((0, wx), (1, wz)):
    for a in range(size):
        b = 0
        while b < size:
            x, z = (b, a) if axis == 0 else (a, b)
            if not wallat(x, z): b += 1; continue
            c = b
            while c < size and wallat(*((c, a) if axis == 0 else (a, c))): c += 1
            for k in range(b, c): store[((k, a) if axis == 0 else (a, k))] = c - b
            b = c
wruns = sorted(max(wx.get(t, 1), wz.get(t, 1)) for t in walls)
dead = sum(1 for x, z in opens if sum(openat(x+dx, z+dz) for dx, dz in ((1,0),(-1,0),(0,1),(0,-1))) == 1)
# enclosed rooms: flood regions in open tiles, counting only regions fully inside the render
seen = set(); enclosed = 0
for s in opens:
    if s in seen: continue
    stack = [s]; seen.add(s); region = []
    while stack:
        x, z = stack.pop(); region.append((x, z))
        for dx, dz in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, nz = x+dx, z+dz
            if openat(nx, nz) and (nx, nz) not in seen: seen.add((nx, nz)); stack.append((nx, nz))
    if len(region) < 400: enclosed += len(region)
# "room-ness" via sight: tiles whose x-run and z-run are both <= 12 and >= 3 count as in a room-sized space
def pct(a, p): return a[min(len(a)-1, int(len(a)*p))] if a else 0
print(f"level {want}: tiles {len(tiles)}  wall% {100*len(walls)/max(1,len(tiles)):.1f}  "
      f"view p10 {pct(view,0.1)} p50 {pct(view,0.5)} p90 {pct(view,0.9)}  width p50 {pct(width,0.5)}  "
      f"dead% {100*dead/max(1,len(opens)):.1f}  wallrun p50 {pct(wruns,0.5)} p90 {pct(wruns,0.9)}  "
      f"small-pocket% {100*enclosed/max(1,len(opens)):.1f}")
