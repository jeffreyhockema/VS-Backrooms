"""Renders hubvault.bin (from `mapgen <seed> <cells> hubvault x z [r]`, layout version 9) to pictures of the Hub's
rounded tunnels, with the vault pieces' real geometry read from their shapes (assets/backrooms/shapes/block/hub/vault-*):

    python render_hubvault.py slice x|z <coord> out.png        a cross-section through the dump at world x (or z) = coord,
                                                               16 px a block: walls, doors and sigils, lamps, the vault
    python render_hubvault.py plan out.png                     the roof seen from below (a reflected plan), shaded by
                                                               height: how the tunnels' vaults meet at junctions
    python render_hubvault.py view x z heading out.png [eye]   a view down the tunnels from x, z (blocks, eye height
                                                               `eye` over the road, default 1.6), heading in degrees
                                                               (0 north, 90 east), lit by the wall lamps: grey shapes only

Run it where hubvault.bin is (it is written to the working folder).
"""
import glob
import json
import math
import os
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SHAPES = os.path.join(HERE, "..", "..", "assets", "backrooms", "shapes", "block", "hub")
GEN = os.path.join(HERE, "..", "..", "src", "Worldgen", "WorldLayout.HubVault.g.cs")

FLOOR, WALL, PIT, DOOR = 0, 1, 5, 7
SIDEWALK, POOLTILE = 153, None
FAN, SIGNAL = (70, 71), (72, 73)
LAMP, DEADLAMP = 1, 2
FROM, TOP = 6, 10
FACINGS = {2: "north", 1: "east", 3: "south", 0: "west"}  # ArchPier: West, East, North, South


def piece_names():
    text = open(GEN, encoding="utf-8").read()
    line = next(l for l in text.splitlines() if "HubVaultPieces =" in l)
    return [s.strip().strip('"') for s in line.split("{", 1)[1].rsplit("}", 1)[0].split(",")]


def heightmap(name, facing):
    """The piece's 16 x 16 heightmap seen from above, [x][z] in world terms: where its solid begins (16 = open)."""
    shape = json.load(open(os.path.join(SHAPES, f"vault-{name}.json"), encoding="utf-8"))
    hm = np.full((16, 16), 16, dtype=np.int32)
    for e in shape["elements"]:
        (x1, y1, z1), (x2, y2, z2) = e["from"], e["to"]
        for x in range(int(x1), int(x2)):
            for z in range(int(z1), int(z2)):
                hm[x, z] = min(hm[x, z], int(y1))
    out = np.empty_like(hm)
    for x in range(16):
        for z in range(16):
            if facing == "north":
                wx, wz = x, z
            elif facing == "south":
                wx, wz = 15 - x, 15 - z
            elif facing == "east":
                wx, wz = 15 - z, x
            else:
                wx, wz = z, 15 - x
            out[wx, wz] = hm[x, z]
    return out


def load():
    with open("hubvault.bin", "rb") as f:
        assert f.read(4) == b"HUBV"
        x0, z0, size = struct.unpack("<iii", f.read(12))
        raw = np.frombuffer(f.read(size * size * 21), dtype=np.uint8).reshape(size, size, 21)
    return x0, z0, size, raw


class Scene:
    """The dump as columns: per 1/16-block pixel column, the floor and roof heights (rel units), solid where they meet."""

    def __init__(self):
        self.x0, self.z0, self.size, self.raw = load()
        names = piece_names()
        self.maps = {}
        for p in range(2, len(names)):
            for d, fname in FACINGS.items():
                self.maps[(p, d)] = heightmap(names[p], fname)
        n = self.size * 16
        self.floor = np.zeros((n, n), dtype=np.float32)  # [x][z]
        self.roof = np.zeros((n, n), dtype=np.float32)
        self.kind = np.zeros((self.size, self.size), dtype=np.uint8)
        self.lamps = []
        for bz in range(self.size):
            for bx in range(self.size):
                t = self.raw[bz, bx]
                kind, floor, height, over, detail, depth, pier, vault = t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[9]
                self.kind[bx, bz] = kind
                sx, sz = bx * 16, bz * 16
                if kind not in (FLOOR, PIT):
                    continue
                fl = 1.5 if floor == SIDEWALK else 1.0
                self.floor[sx:sx + 16, sz:sz + 16] = fl
                if vault:
                    roof = np.full((16, 16), TOP + 1.0, dtype=np.float32)
                    for i in range(TOP - FROM, -1, -1):
                        c = t[10 + i]
                        rel = FROM + i
                        if c == 1:
                            roof[:] = rel
                        elif c >= 2:
                            hm = self.maps[(c, t[15 + i])]
                            roof = np.where(hm < 16, rel + hm / 16.0, roof)
                    self.roof[sx:sx + 16, sz:sz + 16] = roof
                else:
                    self.roof[sx:sx + 16, sz:sz + 16] = (height or 7) + 1
                if detail in (LAMP, DEADLAMP):
                    self.lamps.append((bx + 0.5, depth + 0.5, bz + 0.5, pier, detail == LAMP))


def slice_image(sc, axis, coord, out):
    s = 16
    if axis == "x":
        line = [(coord - sc.x0, k) for k in range(sc.size)]
    else:
        line = [(k, coord - sc.z0) for k in range(sc.size)]
    img = Image.new("RGB", (sc.size * s, 13 * s), (12, 10, 8))
    d = ImageDraw.Draw(img)
    for k, (bx, bz) in enumerate(line):
        t = sc.raw[bz, bx]
        kind, floor, height, over, detail, depth, pier, pattern, under, vault = t[:10]
        x = k * s
        def cell(rel, colour):
            d.rectangle([x, (12 - rel) * s, x + s - 1, (13 - rel) * s - 1], fill=colour)
        cell(0, (90, 88, 84))
        if kind == DOOR:
            for rel in range(1, 5):
                cell(rel, (176, 160, 130))
            cell(5, (150, 140, 120))
            d.ellipse([x + 4, (12 - 5) * s + 4, x + 12, (13 - 5) * s - 4], outline=(70, 60, 50))
            for rel in range(6, 11):
                cell(rel, (140, 137, 130))
            for rel in range(11, 13):
                cell(rel, (70, 70, 70))
            continue
        if kind not in (FLOOR, PIT):
            for rel in range(1, 11):
                cell(rel, (140, 137, 130))
            for rel in range(11, 13):
                cell(rel, (70, 70, 70))
            continue
        if floor == SIDEWALK:
            d.rectangle([x, 11 * s + s // 2, x + s - 1, 12 * s - 1], fill=(178, 172, 160))
        else:
            cell(0, (48, 46, 44))
        # The roof over this block along the slice's middle row of pixels
        for px in range(16):
            gx = bx * 16 + (px if axis == "z" else 8)
            gz = bz * 16 + (px if axis == "x" else 8)
            r = sc.roof[gx, gz]
            y = int(round((13 - r) * s))
            d.line([x + px, 0, x + px, y - 1], fill=(117, 114, 108))
        if detail in (LAMP, DEADLAMP):
            cell_y = (12 - depth) * s
            d.rectangle([x + 3, cell_y + 4, x + 12, cell_y + 12], fill=(255, 190, 80) if detail == LAMP else (90, 60, 30))
        if over in FAN or over in SIGNAL:
            rel = TOP - 1 if vault else height
            cell_y = (12 - rel) * s
            d.rectangle([x + 1, cell_y + 3, x + 15, cell_y + 12], fill=(170, 175, 178) if over in FAN else (30, 30, 30))
    # A rel scale on the left
    for rel in range(13):
        d.line([0, (13 - rel) * s - 1, 3, (13 - rel) * s - 1], fill=(200, 200, 200))
    img = img.resize((img.width * 3, img.height * 3), Image.NEAREST)
    img.save(out)
    print(f"{out}: slice at {axis} = {coord}")


def plan_image(sc, out):
    roof = sc.roof.T  # [z][x]
    solid = (roof <= 0)
    gy, gx = np.gradient(roof)
    shade = np.clip(0.75 + 0.9 * (gx * 0.6 - gy * 0.4), 0.2, 1.3)
    level = np.clip((roof - 6) / 5.0, 0, 1)
    r = (60 + 150 * level) * shade
    g = (55 + 120 * level) * shade
    b = (50 + 70 * level) * shade
    rgb = np.stack([r, g, b], axis=-1)
    rgb[solid] = (14, 12, 10)
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    img.save(out)
    print(f"{out}: roof from below, {sc.size} blocks across (pale = high, 1 px = 1/16 block)")


def view_image(sc, x, z, heading, out, eye=1.6, w=800, h=450, fov=75):
    """A ray march through the columns: floor, roof and walls in grey, lit by the lamps (inverse square) and a little
    ambient, fogged orange with distance."""
    n = sc.size * 16
    ex, ez = (x - sc.x0) * 16.0, (z - sc.z0) * 16.0
    ey = (1.0 + eye) * 16.0
    hd = math.radians(heading)
    fwd = np.array([math.sin(hd), 0, -math.cos(hd)])
    right = np.array([math.cos(hd), 0, math.sin(hd)])
    up = np.array([0, 1.0, 0])
    tan = math.tan(math.radians(fov) / 2)
    ys, xs = np.mgrid[0:h, 0:w]
    u = (xs + 0.5) / w * 2 - 1
    v = 1 - (ys + 0.5) / h * 2
    dirs = fwd[None, None, :] + u[..., None] * tan * right[None, None, :] + v[..., None] * tan * (h / w) * up[None, None, :]
    dirs /= np.linalg.norm(dirs, axis=-1, keepdims=True)
    dx, dy, dz = dirs[..., 0].ravel(), dirs[..., 1].ravel(), dirs[..., 2].ravel()
    m = dx.size
    px, py, pz = np.full(m, ex), np.full(m, ey), np.full(m, ez)
    hit = np.zeros(m, dtype=np.int8)  # 0 none, 1 floor, 2 roof, 3 wall
    dist = np.zeros(m)
    floor16, roof16 = sc.floor * 16, sc.roof * 16
    step = 0.5
    for i in range(int(70 * 16 / step)):
        live = hit == 0
        if not live.any():
            break
        px[live] += dx[live] * step
        py[live] += dy[live] * step
        pz[live] += dz[live] * step
        dist[live] += step
        ix = np.clip(px.astype(int), 0, n - 1)
        iz = np.clip(pz.astype(int), 0, n - 1)
        out_of = (px < 0) | (pz < 0) | (px >= n) | (pz >= n)
        fl, rf = floor16[ix, iz], roof16[ix, iz]
        wall = live & ((rf <= fl) | out_of)
        flo = live & ~wall & (py <= fl)
        rof = live & ~wall & (py >= rf)
        hit[wall] = 3
        hit[flo] = 1
        hit[rof] = 2
    # Normals: floor up; walls from where the ray came in; roof from the roof's slope
    ix = np.clip(px.astype(int), 0, n - 1)
    iz = np.clip(pz.astype(int), 0, n - 1)
    gxr = np.gradient(roof16, axis=0)
    gzr = np.gradient(roof16, axis=1)
    nx, ny, nz = np.zeros(m), np.zeros(m), np.zeros(m)
    ny[hit == 1] = 1
    rmask = hit == 2
    nx[rmask], nz[rmask], ny[rmask] = gxr[ix[rmask], iz[rmask]], gzr[ix[rmask], iz[rmask]], -1
    # A wall's face is the side of its block the ray crossed into last (from one step back)
    wmask = hit == 3
    qx = np.clip((px - dx * step).astype(int), 0, n - 1)
    ax = roof16[qx, iz] > floor16[qx, iz]  # stepping back along x alone leaves the wall: its face looks along x
    nx[wmask & ax] = -np.sign(dx[wmask & ax])
    nz[wmask & ~ax] = -np.sign(dz[wmask & ~ax])
    norm = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-9
    nx, ny, nz = nx / norm, ny / norm, nz / norm
    light = np.full(m, 0.10)
    for (lx, ly, lz, pier, on) in sc.lamps:
        if not on:
            continue
        Lx, Ly, Lz = lx * 16 - px, (ly + 0.2) * 16 - py, lz * 16 - pz
        d2 = (Lx * Lx + Ly * Ly + Lz * Lz) / 256.0 + 0.5
        dot = np.clip((Lx * nx + Ly * ny + Lz * nz) / np.sqrt(d2 * 256.0), 0, 1)
        light += 5.0 * dot / d2
    base = np.where(hit == 1, 0.55, np.where(hit == 2, 0.75, 0.85))
    val = np.clip(base * light, 0, 1.4)
    fog = np.exp(-dist / 16.0 / 30.0)
    col = np.stack([val * 255 * 1.0, val * 255 * 0.72, val * 255 * 0.42], axis=-1)
    fogc = np.array([82, 54, 23])
    col = col * fog[:, None] + fogc[None, :] * (1 - fog[:, None])
    col[hit == 0] = fogc
    img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8).reshape(h, w, 3))
    img.save(out)
    print(f"{out}: view from {x},{z} heading {heading}")


def main():
    mode = sys.argv[1]
    sc = Scene()
    if mode == "slice":
        slice_image(sc, sys.argv[2], int(sys.argv[3]), sys.argv[4])
    elif mode == "plan":
        plan_image(sc, sys.argv[2])
    elif mode == "view":
        view_image(sc, float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5],
                   float(sys.argv[6]) if len(sys.argv) > 6 else 1.6)


if __name__ == "__main__":
    main()
