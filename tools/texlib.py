"""Shared texture helpers that need a little more than flat noise: tileable veined marble, soft gradients."""
import math
import random

from PIL import Image

S = 32


def _periodic_noise(seed, octaves=4):
    """A tileable smooth noise field on the 32x32 grid: a sum of sine waves with whole-number frequencies."""
    rng = random.Random(seed)
    waves = []
    for o in range(octaves):
        for _ in range(3):
            fx, fy = rng.randint(1, 2 + o * 2), rng.randint(0, 2 + o * 2)
            if rng.random() < 0.5:
                fx = -fx
            waves.append((fx, fy, rng.uniform(0, 2 * math.pi), 0.6 ** o))
    total = sum(w[3] for w in waves)
    field = [[0.0] * S for _ in range(S)]
    for y in range(S):
        for x in range(S):
            v = 0.0
            for fx, fy, ph, amp in waves:
                v += amp * math.sin(2 * math.pi * (fx * x + fy * y) / S + ph)
            field[y][x] = v / total
    return field


def marble(base, vein, seed, veins=1, sharpness=5.0, mottle=0.06, turbulence=3.0):
    """Veined marble: soft mottling over the base colour, with veins that wander where a turbulent wave crosses zero.
    Tiles seamlessly, so a floor or a column does not show block edges."""
    turb = _periodic_noise(seed, 3)
    mott = _periodic_noise(seed + 1, 2)
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            # Veins run diagonally; whole-number frequencies keep them continuous across the edges
            w = math.sin(2 * math.pi * veins * (x + y) / S + turbulence * turb[y][x])
            t = math.exp(-sharpness * abs(w))  # 1 on a vein, falling off fast
            m = 1 + mottle * mott[y][x]
            px[x, y] = tuple(max(0, min(255, int((base[k] * (1 - t) + vein[k] * t) * m))) for k in range(3)) + (255,)
    return img


def vertical_gradient(top, bottom, height=S, width=S):
    img = Image.new("RGBA", (width, height))
    px = img.load()
    for y in range(height):
        t = y / max(1, height - 1)
        c = tuple(int(top[k] + (bottom[k] - top[k]) * t) for k in range(3)) + (255,)
        for x in range(width):
            px[x, y] = c
    return img
