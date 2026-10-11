"""Picks camera spots with long, furnished views from the layout harness's tile dump.

    python pick.py <level> <cx> <cz> [n_cells] [count]

Runs mapgen in a scratch dir (seed fixed below), reads tiles.bin and prints
    x z heading score raylen props
for the best standing spots in that level (compass heading, 0 N / 90 E).
"""
import math, os, struct, subprocess, sys

SEED = os.environ.get("SEED", "1672613597")
MAPGEN = os.environ.get("MAPGEN", os.path.join(os.environ["TEMP"], "backrooms-build", "mapgen-shots", "mapgen.exe"))
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "harness")

FLOOR, WALL, DOORWAY, ARCHWIN, ARCHDOOR, PIT, WATER = 0, 1, 2, 3, 4, 5, 6


def load(level, cx, cz, n):
    os.makedirs(WORK, exist_ok=True)
    mx, mz = cx // 32, cz // 32
    subprocess.run([MAPGEN, SEED, str(n), "at", str(mx), str(mz)], cwd=WORK, check=True, capture_output=True)
    d = open(os.path.join(WORK, "tiles.bin"), "rb").read()
    size = struct.unpack_from("<i", d, 0)[0]
    nc = size // 32
    m0x, m0z = mx - n // 2, mz - n // 2
    grid = {}
    off = 4
    for gz in range(nc):
        for gx in range(nc):
            for i in range(1024):
                k, fl, ce, flags, lvl, pat, var = d[off:off + 7]
                off += 7
                x = (m0x + gx) * 32 + i % 32
                z = (m0z + gz) * 32 + i // 32
                grid[(x, z)] = (k, fl, ce, flags, lvl, pat, var)
    return grid, (m0x * 32, m0z * 32, size)


def pick(level, cx, cz, n=14, count=8, maxlen=56, need_flag=0):
    grid, (x0, z0, size) = load(level, cx, cz, n)

    def t(x, z):
        return grid.get((x, z))

    def passable(c):
        return c is not None and c[4] == level and c[0] in (FLOOR, DOORWAY, ARCHDOOR)

    def standable(c):
        return passable(c) and c[0] == FLOOR and c[6] == 0 and not (c[3] & 1) and not (c[3] & 2)

    dirs = [(math.sin(math.radians(a)), -math.cos(math.radians(a)), a) for a in range(0, 360, 10)]
    cands = []
    for z in range(z0 + 4, z0 + size - 4, 2):
        for x in range(x0 + 4, x0 + size - 4, 2):
            c = t(x, z)
            if not standable(c) or (need_flag and not (c[3] & need_flag)):
                continue
            # openness around the spot
            open_n = sum(1 for dz in range(-3, 4) for dx in range(-3, 4) if passable(t(x + dx, z + dz)))
            if open_n < 12:
                continue
            best = None
            for dx, dz, a in dirs:
                length, props, lit = 0, 0, 0
                while length < maxlen:
                    px = int(math.floor(x + 0.5 + dx * (length + 1)))
                    pz = int(math.floor(z + 0.5 + dz * (length + 1)))
                    cc = t(px, pz)
                    if not passable(cc):
                        break
                    length += 1
                    # count furniture / props visible beside the ray within the first 30 blocks
                    if length <= 30:
                        for s in (-2, -1, 1, 2):
                            qx = int(math.floor(px + 0.5 - dz * s))
                            qz = int(math.floor(pz + 0.5 + dx * s))
                            q = t(qx, qz)
                            if q is not None and q[4] == level and q[0] == FLOOR and q[6] >= 40:
                                props += 1
                            if q is not None and q[4] == level and q[0] == WALL and q[6] >= 40:
                                props += 0.5
                        if cc[2] in (1, 2, 7):
                            lit += 1
                # side openness near the camera, so the view is not a 1-wide slot
                side = 0
                for k in range(1, 9):
                    px = int(math.floor(x + 0.5 + dx * k)); pz = int(math.floor(z + 0.5 + dz * k))
                    for s in (-2, 2):
                        if passable(t(int(math.floor(px + 0.5 - dz * s)), int(math.floor(pz + 0.5 + dx * s)))):
                            side += 1
                score = min(length, 44) + 0.6 * min(props, 20) + 0.3 * side + 0.15 * lit
                if length < 10:
                    continue
                if best is None or score > best[0]:
                    best = (score, a, length, props)
            if best:
                cands.append((best[0], x, z, best[1], best[2], best[3]))
    cands.sort(reverse=True)
    out = []
    for s, x, z, a, length, props in cands:
        if all(abs(x - ox) + abs(z - oz) > 28 for _, ox, oz, *_ in out):
            out.append((s, x, z, a, length, props))
        if len(out) >= count:
            break
    return out


if __name__ == "__main__":
    level = int(sys.argv[1]); cx = int(sys.argv[2]); cz = int(sys.argv[3])
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 14
    count = int(sys.argv[5]) if len(sys.argv) > 5 else 8
    flag = 64 if len(sys.argv) > 6 and sys.argv[6] == 'grand' else 0
    for s, x, z, a, length, props in pick(level, cx, cz, n, count, need_flag=flag):
        print(f"{x + 0.5} {z + 0.5} {a} score={s:.1f} ray={length} props={props:.0f}")
