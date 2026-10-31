"""Level 120 ("Broken Servos"): the Misglitch's sounds (entity/120/) and the level's ambient and effect sounds
(ambient/120/; serverhum.ogg is made by gen_120.py). All synthesised, mono OGG. The Misglitch is digital: bit-crushed,
sample-rate-reduced noise gated in 20-60 ms chunks, a corrupted human voice under it, granulated and stuttered. Loops
(voidtone, hallway) are seamless: noise is filtered over the whole loop with the FFT (circular) and every tone has a whole
number of cycles in the loop. Run from the repo root:  python tools/gen_120_sounds.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from gen_entity_sounds import RATE, band, place, reverb, seconds, thud, vowel  # noqa: E402
from gen_level_sounds import write as write_ogg  # noqa: E402

WRITTEN = []


def write(folder, name, signal, peak, fade=True):
    write_ogg(folder, name, signal, peak, fade)
    WRITTEN.append(f"{folder}/{name}")


def norm(x):
    return x / max(1e-9, np.max(np.abs(x)))


def crush(x, bits, hold):
    """Bit-crush and sample-rate reduction: every `hold`th sample kept, quantised to `bits` bits."""
    y = np.repeat(x[::hold], hold)[: len(x)]
    q = 2 ** (bits - 1)
    return np.round(norm(y) * q) / q


def gate(n, rng, lo=0.02, hi=0.06, p_on=0.6):
    """A 0/1 gate stuttering on and off in chunks of lo..hi seconds."""
    g = np.zeros(n)
    i = 0
    on = True
    while i < n:
        L = int(rng.uniform(lo, hi) * RATE)
        if on:
            g[i:i + L] = 1.0
        on = rng.random() < p_on
        i += L
    return g


def resample(g, ratio):
    idx = np.arange(0, len(g) - 1, ratio)
    return np.interp(idx, np.arange(len(g)), g)


def granulate(x, rng, n_out, grain=0.05, shifts=(1.0,), repeats=(1,), advance=0.7):
    """Grains of x laid out along the output, each repeated and pitch-jumped: a voice stuttering."""
    out = np.zeros(n_out)
    G = int(grain * RATE)
    pos = 0
    while pos < n_out:
        src = int(pos / n_out * max(1, len(x) - G))
        g = x[src:src + G] * np.hanning(len(x[src:src + G]))
        for _ in range(int(rng.choice(repeats))):
            g2 = resample(g, float(rng.choice(shifts)))
            e = min(len(g2), n_out - pos)
            if e <= 0:
                break
            out[pos:pos + e] += g2[:e]
            pos += int(len(g2) * advance)
    return out


def clicks_at_edges(g, amp, rng):
    out = np.zeros(len(g))
    for i in np.where(np.diff(g) > 0)[0]:
        L = min(int(0.0012 * RATE), len(g) - i - 1)
        out[i:i + L] += amp * rng.choice((-1, 1)) * np.linspace(1, 0, L)
    return out


def wrap_place(out, sound, at):
    i = int(at * RATE) % len(out)
    first = min(len(sound), len(out) - i)
    out[i:i + first] += sound[:first]
    if len(sound) > first:
        out[:len(sound) - first] += sound[first:]


def steps(n, rng, every, spread):
    """A contour that holds a random value for `every` seconds at a time (a stuttering pitch)."""
    k = max(1, int(every * RATE))
    v = rng.uniform(-spread, spread, size=n // k + 2)
    return np.repeat(v, k)[:n]


VOICE = [(550, 160, 1.0), (1200, 220, 0.6), (2600, 300, 0.3)]


# ======================= The Misglitch =======================

def static_burst(rng, length, hold, bits, f0, p_on, lo=300, hi=9000, formants=VOICE):
    n = int(length * RATE)
    t = np.arange(n) / RATE
    noise = crush(norm(band(rng.normal(size=n), lo, hi)), bits, hold)
    g = gate(n, rng, 0.02, 0.06, p_on)
    f = f0 * (1 + steps(n, rng, 0.04, 0.35))
    v = norm(vowel(t, f, formants, 0.1, rng))
    v = crush(v, 3, 3)
    gv = gate(n, rng, 0.03, 0.08, 0.7)
    out = 0.8 * noise * g + 0.3 * v * gv + clicks_at_edges(g, 0.9, rng)
    env = np.minimum(1, t / 0.03) * (0.75 + 0.25 * np.sin(2 * np.pi * 3 * t / length * 0.5)) * np.clip((length - t) / 0.08, 0, 1)
    return out * env


def hunt(rng):
    n = int(1.5 * RATE)
    t = np.arange(n) / RATE
    f0 = 110 + 90 * (t / 1.5) ** 1.3 + 4 * np.sin(2 * np.pi * 5.5 * t)
    # a breathy moan: aa opening to oh to ee as it rises
    base = norm(vowel(t, f0, [(650, 170, 1.0), (1100, 220, 0.6), (2500, 320, 0.3)], 0.35, rng))
    base2 = norm(vowel(t, f0, [(350, 120, 1.0), (900, 160, 0.5), (2300, 300, 0.2)], 0.3, rng))
    mix = np.clip(t / 1.5, 0, 1)
    voice = base * (1 - mix) + base2 * mix
    gr = granulate(voice, rng, n, 0.055, shifts=(1.0, 1.0, 0.75, 1.5, 2.0), repeats=(1, 2, 3), advance=0.8)
    out = crush(gr, 5, 3) * (0.35 + 0.65 * (t / 1.5) ** 1.2)
    out += 0.25 * crush(norm(band(rng.normal(size=n), 800, 8000)), 4, 5) * gate(n, rng, 0.02, 0.05, 0.5) * (t / 1.5)
    return out * np.clip((1.5 - t) / 0.05, 0, 1)


def slice_(rng):
    n = int(0.5 * RATE)
    t = np.arange(n) / RATE
    noise = rng.normal(size=n)
    out = np.zeros(n)
    frame = int(0.02 * RATE)
    for i, s in enumerate(range(0, n - frame, frame)):
        c = 1800 + 7000 * min(1.0, s / (0.22 * RATE))
        seg = band(noise[s:s + frame] * np.hanning(frame), c * 0.7, c * 1.4)
        out[s:s + frame] += seg
    whoosh = norm(out) * np.sin(np.pi * np.clip(t / 0.3, 0, 1)) ** 2 * (t < 0.3)
    wet = norm(band(rng.normal(size=n), 120, 900)) * np.exp(-np.abs(t - 0.17) * 22) * 0.7
    snap = norm(band(rng.normal(size=n), 4000, 14000)) * np.where(t >= 0.16, np.exp(-(t - 0.16) * 60), 0)
    ring = np.where(t >= 0.16, np.sin(2 * np.pi * 5200 * t) * np.exp(-(t - 0.16) * 70), 0) * 0.35
    return 0.55 * whoosh + wet + 1.3 * snap + ring


def hurt(rng):
    n = int(0.4 * RATE)
    t = np.arange(n) / RATE
    f0 = 320 - 130 * t / 0.4 + 40 * steps(n, rng, 0.05, 1.0)
    v = norm(vowel(t, f0, [(800, 200, 1.0), (1300, 250, 0.6), (2800, 320, 0.3)], 0.2, rng))
    gr = granulate(v, rng, n, 0.035, shifts=(1.0, 1.3, 0.8, 1.7), repeats=(1, 2, 2, 3), advance=0.75)
    out = crush(gr, 4, 2) * np.exp(-t * 3.5)
    out += 0.3 * crush(norm(band(rng.normal(size=n), 500, 8000)), 3, 4) * gate(n, rng, 0.02, 0.04, 0.5) * np.exp(-t * 6)
    return out


def death(rng):
    n = int(1.5 * RATE)
    t = np.arange(n) / RATE
    f0 = 170 - 80 * (t / 1.5) ** 0.8 + 3 * np.sin(2 * np.pi * 4 * t)
    v = norm(vowel(t, f0, [(650, 170, 1.0), (1100, 220, 0.5), (2400, 300, 0.25)], 0.3, rng))
    thin = np.clip(1 - t / 1.0, 0, 1)
    voice = np.zeros(n)
    for i in range(0, n, int(0.04 * RATE)):
        e = min(n, i + int(0.04 * RATE))
        bits = int(round(8 - 5 * min(1, t[i] / 1.0)))
        voice[i:e] = crush(v[i:e], max(2, bits), 1 + int(5 * min(1, t[i] / 1.0)))
    gv = np.where(gate(n, rng, 0.02, 0.06, 0.55 + 0.4 * thin[0]) > 0, 1.0, 0.0)
    keep = np.interp(t, [0, 0.4, 1.0], [1.0, 0.8, 0.0])
    gv = np.where(rng.random(n // 100 + 1).repeat(100)[:n] < keep, gv, 0)
    stat = crush(norm(band(rng.normal(size=n), 400, 9000)), 4, 3) * gate(n, rng, 0.02, 0.05, 0.6)
    stat *= np.interp(t, [0, 0.3, 0.9, 1.1], [0.1, 0.8, 0.5, 0.0])
    out = voice * thin ** 0.7 * gv * 0.7 + stat * 0.45
    # sparse clicks and silence
    for at in sorted(rng.uniform(0.7, 1.45, size=9)):
        k = rng.integers(2, 5)
        for j in range(k):
            L = int(0.0015 * RATE)
            c = rng.choice((-1, 1)) * np.linspace(1, 0, L) * rng.uniform(0.3, 0.9) * (1 - (at - 0.7) / 0.9)
            place(out, c, at + j * 0.0035)
    return out


def step(rng):
    n = int(0.25 * RATE)
    t = np.arange(n) / RATE
    f = 600 + 2400 * (t / 0.12) ** 1.5
    f = np.where(t < 0.12, f, 1500)
    ph = 2 * np.pi * np.cumsum(f) / RATE
    tone = np.sign(np.sin(ph)) * 0.5 + np.sin(ph) * 0.5
    env = np.where(t < 0.12, np.minimum(1, t / 0.004) * np.clip((0.12 - t) / 0.02, 0, 1), 0)
    out = crush(tone * env, 5, 2)
    tail = np.sin(2 * np.pi * 1500 * t) * np.where(t > 0.15, np.exp(-(t - 0.15) * 70), 0) * 0.3
    click = np.zeros(n)
    L = int(0.002 * RATE)
    click[:L] = np.linspace(1, -1, L) * 1.2
    return out + crush(tail, 4, 3) + click


# ======================= The level =======================

def hdd(rng, length):
    n = int(length * RATE)
    t = np.arange(n) / RATE
    whir = 0.08 * norm(band(rng.normal(size=n), 200, 1400)) * (0.7 + 0.3 * np.sin(2 * np.pi * 120 * t)) + 0.05 * np.sin(2 * np.pi * 118 * t)
    whir *= np.minimum(1, t / 0.05) * np.clip((length - t) / 0.1, 0, 1)
    out = whir.copy()
    at = 0.02
    while at < length - 0.03:
        burst = int(rng.integers(1, 6))
        for _ in range(burst):
            L = int(rng.uniform(0.004, 0.012) * RATE)
            tt = np.arange(L) / RATE
            f = rng.uniform(2000, 8000)
            c = np.sin(2 * np.pi * f * tt + rng.uniform(0, 6)) * np.exp(-tt * rng.uniform(500, 1200)) * rng.uniform(0.4, 1.0)
            place(out, c, at)
            at += rng.uniform(0.006, 0.035)
        at += rng.choice((rng.uniform(0.03, 0.09), rng.uniform(0.1, 0.22)))
    return out


def relay(rng):
    n = int(0.5 * RATE)
    t = np.arange(n) / RATE
    out = np.zeros(n)
    place(out, thud(0.2, 78, rng, 0.0) * 1.1, 0.0)
    place(out, norm(band(rng.normal(size=int(0.05 * RATE)), 700, 5000)) * np.exp(-seconds(0.05) * 90) * 0.9, 0.0)
    place(out, 0.8 * thud(0.15, 120, rng, 0.2), 0.022)      # the armature slaps home
    ring = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, a, d in ((1830, 0.3, 16), (3140, 0.22, 22), (4720, 0.12, 30), (860, 0.18, 12)))
    out += ring * np.minimum(1, t / 0.002)
    return reverb(out, 0.15)[:n]


def fanspin(rng):
    n = int(4.0 * RATE)
    t = np.arange(n) / RATE
    up = np.clip(t / 1.5, 0, 1) ** 1.6
    down = np.clip((t - 2.3) / 1.7, 0, 1)
    speed = up * (1 - 0.75 * down ** 0.8)
    f = 70 + 450 * speed
    ph = 2 * np.pi * np.cumsum(f) / RATE
    tone = np.sin(ph) + 0.45 * np.sin(2 * ph + 0.5) + 0.2 * np.sin(3 * ph) + 0.12 * np.sin(5 * ph)
    blade = tone * (0.8 + 0.2 * np.sin(np.cumsum(f * 0.1) * 2 * np.pi / RATE))
    air = norm(band(rng.normal(size=n), 250, 4500)) * (0.15 + 0.85 * speed ** 1.2)
    env = np.minimum(1, t / 0.15) * np.clip((4.0 - t) / 0.6, 0, 1)
    return (0.35 * blade * (0.15 + speed) + 0.3 * air) * env


def farstatic(rng):
    x = static_burst(rng, 1.5, 4, 4, 130, 0.6, lo=300, hi=7000)
    x = norm(band(x, 150, 1800))
    return reverb(x, 0.6, taps=((0.05, 0.6), (0.11, 0.5), (0.19, 0.4), (0.31, 0.3), (0.47, 0.2)))[: len(x)]


def voidtone(rng):
    n = 8 * RATE
    t = np.arange(n) / RATE
    tone = np.sin(2 * np.pi * 1900 * t) + 0.35 * np.sin(2 * np.pi * 1903 * t + 0.7)   # 3 Hz apart: 24 beats in the loop
    tone *= 1 + 0.06 * np.sin(2 * np.pi * 0.25 * t)
    air = norm(band(rng.normal(size=n), 1500, 9000))
    return tone * 0.9 + 0.02 * air


def hallway(rng):
    n = 8 * RATE
    t = np.arange(n) / RATE
    rumble = norm(band(rng.normal(size=n), 18, 120)) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.25 * t + 1))
    whistle = np.sin(2 * np.pi * 6000 * t) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.375 * t))
    return rumble + 0.04 * whistle


def boot(rng):
    n = int(2.5 * RATE)
    t = np.arange(n) / RATE
    out = np.zeros(n)
    # the CRT degauss: a thunk and a decaying 60 Hz buzz with its harmonics
    thunk = thud(0.3, 55, rng, 0.5) * 1.2
    place(out, thunk, 0.0)
    buzz = (np.sin(2 * np.pi * 60 * t) + 0.5 * np.sin(2 * np.pi * 120 * t) + 0.3 * np.sin(2 * np.pi * 180 * t) + 0.2 * norm(band(rng.normal(size=n), 40, 500)))
    out += 0.35 * buzz * np.exp(-t * 6) * (t < 0.7) * (1 + 0.4 * np.sin(2 * np.pi * 14 * t))
    # the drive spinning up: a rising whir, steady, then a few seeks
    s0 = 0.5
    rise = np.clip((t - s0) / 1.2, 0, 1)
    f = 45 + 105 * rise ** 0.8
    ph = 2 * np.pi * np.cumsum(f) / RATE
    whir = (np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph)) * 0.18 + 0.12 * norm(band(rng.normal(size=n), 400, 3000)) * rise
    whir *= (t > s0) * np.minimum(1, (t - s0) / 0.1) * np.where(t > 1.7, 0.55, 1.0)
    out += whir
    for at in (1.78, 1.83, 1.9, 1.94, 2.02):
        L = int(0.006 * RATE)
        tt = np.arange(L) / RATE
        place(out, np.sin(2 * np.pi * rng.uniform(2500, 6000) * tt) * np.exp(-tt * 700) * 0.5, at)
    # POST beep
    be = (t >= 2.1) & (t < 2.3)
    tb = t - 2.1
    sq = np.sin(2 * np.pi * 1000 * tb) + (1 / 3) * np.sin(2 * np.pi * 3000 * tb) + 0.2 * np.sin(2 * np.pi * 5000 * tb)
    out += 0.55 * sq * be * np.minimum(1, tb / 0.004) * np.clip((0.2 - tb) / 0.006, 0, 1)
    return out


def window(rng):
    n = int(1.0 * RATE)
    t = np.arange(n) / RATE
    out = 0.3 * norm(band(rng.normal(size=n), 200, 1500)) * np.sin(np.pi * np.clip(t / 1.0, 0, 1)) ** 2
    ats = np.sort(np.concatenate([rng.uniform(0.04, 0.18, 4), rng.uniform(0.3, 0.62, 6)]))
    for at in ats:
        L = int(rng.uniform(0.006, 0.022) * RATE)
        tt = np.arange(L) / RATE
        c = norm(band(rng.normal(size=L), 2000, 10000)) * np.exp(-tt * rng.uniform(150, 400)) * rng.uniform(0.4, 1.0)
        place(out, c, at)
        if rng.random() < 0.5:
            L2 = int(0.12 * RATE)
            t2 = np.arange(L2) / RATE
            f = rng.uniform(3200, 6500)
            place(out, 0.12 * np.sin(2 * np.pi * f * t2) * np.exp(-t2 * 40), at)
    return out


def trip(rng):
    n = int(0.6 * RATE)
    t = np.arange(n) / RATE
    out = np.zeros(n)
    scuff = norm(band(rng.normal(size=n), 400, 2800)) * np.where(t < 0.16, np.sin(np.pi * np.clip(t / 0.16, 0, 1)) ** 1.3, 0)
    out += 0.5 * scuff
    place(out, thud(0.25, 62, rng, 0.35) * 1.3, 0.21)
    place(out, norm(band(rng.normal(size=int(0.2 * RATE)), 40, 260)) * np.exp(-seconds(0.2) * 22) * 0.8, 0.21)
    place(out, thud(0.18, 85, rng, 0.2) * 0.45, 0.33)
    breath = norm(band(rng.normal(size=n), 600, 2600)) * np.where((t > 0.3) & (t < 0.56), np.sin(np.pi * np.clip((t - 0.3) / 0.26, 0, 1)) ** 2, 0)
    return out + 0.1 * breath


def generate():
    # Entity
    specs = [("misglitch-static1", 2011, 0.7, 3, 5, 120, 0.6), ("misglitch-static2", 2012, 1.1, 2, 4, 150, 0.5),
             ("misglitch-static3", 2013, 0.55, 5, 6, 95, 0.7)]
    for name, seed, length, hold, bits, f0, p_on in specs:
        write("entity/120", name, static_burst(np.random.default_rng(seed), length, hold, bits, f0, p_on), 0.5)
    write("entity/120", "misglitch-hunt", hunt(np.random.default_rng(2020)), 0.55)
    write("entity/120", "misglitch-slice", slice_(np.random.default_rng(2021)), 0.6)
    write("entity/120", "misglitch-hurt", hurt(np.random.default_rng(2022)), 0.5)
    write("entity/120", "misglitch-death", death(np.random.default_rng(2023)), 0.5)
    write("entity/120", "misglitch-step", step(np.random.default_rng(2024)), 0.4)
    # Level
    write("ambient/120", "hdd1", hdd(np.random.default_rng(2031), 0.8), 0.35)
    write("ambient/120", "hdd2", hdd(np.random.default_rng(2032), 1.1), 0.35)
    write("ambient/120", "relay", relay(np.random.default_rng(2033)), 0.55)
    write("ambient/120", "fanspin", fanspin(np.random.default_rng(2034)), 0.4)
    write("ambient/120", "farstatic", farstatic(np.random.default_rng(2035)), 0.25)
    write("ambient/120", "voidtone", voidtone(np.random.default_rng(2036)), 0.25, fade=False)
    write("ambient/120", "hallway", hallway(np.random.default_rng(2037)), 0.12, fade=False)
    write("ambient/120", "boot", boot(np.random.default_rng(2038)), 0.5)
    write("ambient/120", "window", window(np.random.default_rng(2039)), 0.5)
    write("ambient/120", "trip", trip(np.random.default_rng(2040)), 0.55)
    print(f"Level 120 sounds: {len(WRITTEN)} sounds ({', '.join(WRITTEN)})")


if __name__ == "__main__":
    generate()
