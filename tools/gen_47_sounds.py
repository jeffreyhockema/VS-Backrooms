"""Synthesises the sounds of Level 47, "The Adderwood": small snakes' hisses, the Great Adder (hisses, a far roar, a strike,
a slithering loop, a swallow), crows and ravens, the Ophion Occult Order's droning chant and murmuring, an uncanny displacement
in the fog, snapping branches and a distant woodpecker.

Run from the repo root under the asset lock:  bash tools/locked.sh run python tools/gen_47_sounds.py
Writes assets/backrooms/sounds/creature/47/*.ogg and assets/backrooms/sounds/ambient/47/*.ogg.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from oggutil import write_ogg  # noqa: E402

from gen_entity_sounds import RATE, band, place, reverb, seconds, vowel  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
SOUNDS = os.path.join(ROOT, "assets", "backrooms", "sounds")


def write(kind, name, signal, peak=0.8, fade=True):
    """Normalises and writes sounds/<kind>/47/<name>.ogg; loops (fade=False) are not faded at the ends."""
    path = os.path.join(SOUNDS, kind, "47", name + ".ogg")
    signal = np.asarray(signal, dtype=np.float64)
    if fade:
        n = min(len(signal) // 4, int(0.01 * RATE))
        signal[:n] *= np.linspace(0, 1, n)
        signal[-n:] *= np.linspace(1, 0, n)
    signal = peak * signal / max(1e-9, np.max(np.abs(signal)))
    if write_ogg(path, signal, RATE):
        print("wrote", os.path.relpath(path, ROOT))


def smooth(t0, t1, t):
    u = np.clip((t - t0) / (t1 - t0), 0, 1)
    return u * u * (3 - 2 * u)


def loopify(x, n, over):
    """Cuts x (length n + over) to n samples, crossfading the extra tail into the start so the loop is seamless."""
    out = x[:n].copy()
    fade = np.sin(np.linspace(0, np.pi / 2, over))
    out[:over] = x[:over] * fade + x[n:n + over] * fade[::-1]
    return out


def lowpass(x, hi):
    return band(x, 0, hi)


def tilt(x, power):
    """Colours white noise: negative power darkens it, positive brightens."""
    s = np.fft.rfft(x)
    f = np.maximum(np.fft.rfftfreq(len(x), 1 / RATE), 20)
    return np.fft.irfft(s * (f / 1000) ** power, n=len(x))


# ---- Snakes ----

def snake_hiss(seed):
    rng = np.random.default_rng(4700 + seed)
    length = [0.8, 1.05, 0.65][seed - 1]
    t = seconds(length)
    n = len(t)
    noise = band(rng.normal(size=n), 2500 + 400 * seed, 13000)
    noise += 0.5 * band(rng.normal(size=n), 5000, 9000) * (1 + np.sin(2 * np.pi * 3 * t))
    pulse = 1 + 0.3 * np.sin(2 * np.pi * (7 + 2 * seed) * t + seed) + 0.1 * np.sin(2 * np.pi * 23 * t)
    env = smooth(0, 0.18 * length + 0.05, t) * (1 - smooth(0.6 * length, length, t)) ** 1.3
    return noise * pulse * env


def adder_hiss(seed):
    rng = np.random.default_rng(4710 + seed)
    length = [2.4, 2.9][seed - 1]
    t = seconds(length)
    n = len(t)
    swell = smooth(0, 0.45 * length, t) * (1 - smooth(0.55 * length, length, t)) ** 1.5
    wide = tilt(band(rng.normal(size=n), 250, 7000), -0.4)
    sweep = band(rng.normal(size=n), 900, 3200) * (0.5 + 0.5 * np.sin(2 * np.pi * (0.5 + 0.2 * seed) * t))
    rumble = band(rng.normal(size=n), 30, 140) * 3.0 * (1 + 0.4 * np.sin(2 * np.pi * 5 * t))
    breath = band(rng.normal(size=n), 120, 600) * 1.2
    s = (wide + 0.5 * sweep + rumble + breath) * swell * (1 + 0.12 * np.sin(2 * np.pi * 11 * t))
    return reverb(np.concatenate([s, np.zeros(int(0.3 * RATE))]), 0.3)


def adder_roar():
    rng = np.random.default_rng(4720)
    length = 2.5
    t = seconds(length)
    n = len(t)
    env = smooth(0, 0.5, t) * (1 - smooth(1.4, length, t)) ** 1.4
    hiss = band(rng.normal(size=n), 500, 6000) * (0.6 + 0.4 * smooth(0.2, 1.0, t))
    f0 = 38 + 22 * smooth(0, 1.0, t) * (1 - smooth(1.2, 2.5, t)) + 3 * np.sin(2 * np.pi * 1.7 * t)
    growl = vowel(t, f0, [(70, 40, 1.0), (180, 90, 0.8), (420, 160, 0.4), (900, 250, 0.2)], 0.1, rng)
    rattle = 0.6 + 0.4 * np.sin(2 * np.pi * (24 + 12 * np.sin(2 * np.pi * 0.7 * t)) * t)
    growl = growl / np.max(np.abs(growl)) * rattle
    rumble = band(rng.normal(size=n), 20, 60) * (1 + np.sin(2 * np.pi * 8 * t))
    s = (0.9 * hiss / np.std(hiss) * 0.25 * (0.5 + 0.5 * rattle) + 1.6 * growl + rumble / np.max(np.abs(rumble))) * env
    s = lowpass(s, 3500)          # far off: dull, with a hall behind it
    return reverb(np.concatenate([s, np.zeros(int(0.4 * RATE))]), 0.5)


def adder_strike():
    rng = np.random.default_rng(4730)
    t = seconds(0.5)
    n = len(t)
    low = band(rng.normal(size=n), 100, 900)
    mid = band(rng.normal(size=n), 700, 3500)
    high = band(rng.normal(size=n), 2500, 9000)
    sweep = smooth(0.0, 0.3, t)
    whoosh = low * (1 - sweep * 0.5) + mid * sweep + 0.5 * high * smooth(0.15, 0.34, t)
    whoosh *= smooth(0, 0.28, t) ** 1.5 * (1 - smooth(0.34, 0.42, t))
    snap = np.zeros(n)
    tt = seconds(0.14)
    wet = band(rng.normal(size=len(tt)), 600, 4500) * np.exp(-tt * 60)
    wet += 0.5 * band(rng.normal(size=len(tt)), 200, 900) * np.exp(-tt * 30)
    thud = np.sin(2 * np.pi * 75 * tt * (1 - 0.5 * tt / 0.14)) * np.exp(-tt * 22) * 1.2
    place(snap, wet * 1.2 + thud, 0.355)
    return 0.9 * whoosh / np.std(whoosh) * 0.12 + snap


def adder_slither():
    rng = np.random.default_rng(4740)
    length = 4.0
    n = int(length * RATE)
    t = np.arange(n) / RATE
    swish = band(rng.normal(size=n), 80, 700) + 0.6 * band(rng.normal(size=n), 700, 2200)
    # Periodic in 4 s (the filters are circular too): a body dragging, the loudness rising and falling
    am = 0.6 + 0.25 * np.sin(2 * np.pi * 3 * t / length + 1) + 0.15 * np.sin(2 * np.pi * 7 * t / length)
    sig = swish * am
    clicks = np.zeros(n)
    for _ in range(int(length * 70)):
        at = int(rng.integers(0, n))
        w = int(rng.uniform(0.004, 0.02) * RATE)
        k = np.arange(w) / RATE
        lo, hi = rng.uniform(1200, 3000), rng.uniform(4000, 9000)
        g = band(rng.normal(size=w + 64), lo, hi)[:w] * np.exp(-k * rng.uniform(200, 600))
        g *= rng.uniform(0.15, 1.0) * (0.4 + 1.2 * am[at])
        clicks[(np.arange(w) + at) % n] += g * 0.9
    for _ in range(int(length * 6)):
        at = int(rng.integers(0, n))
        w = int(0.06 * RATE)
        k = np.arange(w) / RATE
        g = band(rng.normal(size=w + 64), 150, 1200)[:w] * np.exp(-k * 50) * rng.uniform(0.5, 1.2) * 0.6
        clicks[(np.arange(w) + at) % n] += g
    return sig / np.std(sig) * 0.5 + clicks / max(1e-9, np.std(clicks)) * 0.5


def adder_swallow():
    rng = np.random.default_rng(4750)
    out = np.zeros(int(1.5 * RATE))
    for at, f, size in [(0.12, 130, 1.0), (0.62, 105, 1.1), (1.05, 85, 0.9)]:
        t = seconds(0.34)
        n = len(t)
        env = smooth(0, 0.07, t) * np.exp(-t * 9)
        body = np.sin(2 * np.pi * np.cumsum(f * (1.3 - 0.8 * t / 0.34)) / RATE) * env
        slosh = band(rng.normal(size=n), 150, 1100) * env * (0.5 + 0.5 * np.sin(2 * np.pi * 38 * t))
        bubble = band(rng.normal(size=n), 700, 2200) * np.exp(-t * 25) * (0.5 + 0.5 * np.sin(2 * np.pi * 70 * t))
        place(out, (body * 1.2 + slosh / np.std(slosh) * 0.15 + bubble / np.std(bubble) * 0.04) * size, at)
    return lowpass(out, 3000)


# ---- Birds ----

def caw(rng, length, f_start, f_end, formants, harsh, voiced_noise):
    t = seconds(length)
    n = len(t)
    u = t / length
    f0 = f_start + (f_end - f_start) * u ** 0.8
    f0 = f0 * (1 + 0.03 * np.sin(2 * np.pi * 70 * t)) * (1 + 0.05 * rng.normal())
    voiced = vowel(t, f0, formants, voiced_noise, rng)
    voiced /= np.max(np.abs(voiced))
    rattle = 1 - harsh * (0.5 + 0.5 * np.sin(2 * np.pi * (95 + 25 * rng.random()) * t))
    nasal = band(rng.normal(size=n), 1200, 4800)
    nasal *= 0.35 / np.max(np.abs(nasal))
    env = smooth(0, 0.04, t) * (1 - smooth(0.6 * length, length, t)) ** 1.2 * (0.8 + 0.2 * np.sin(np.pi * u))
    return (voiced + nasal) * rattle * env


def bird_take(seed, kind):
    rng = np.random.default_rng((4760 if kind == "crow" else 4780) + seed)
    out = np.zeros(int(2.5 * RATE))
    at = 0.05
    if kind == "crow":
        count = [2, 3, 1, 2][seed - 1]
        for i in range(count):
            length = rng.uniform(0.25, 0.4)
            f0 = rng.uniform(560, 700)
            c = caw(rng, length, f0, f0 * rng.uniform(0.55, 0.7),
                    [(900, 220, 1.0), (1700, 300, 0.7), (2700, 450, 0.5), (3800, 600, 0.2)], 0.45, 0.35)
            place(out, c * (1 - 0.1 * i), at)
            at += length + rng.uniform(0.12, 0.25)
    else:
        count = [1, 2, 2][seed - 1]
        for i in range(count):
            length = rng.uniform(0.3, 0.5)
            f0 = rng.uniform(230, 300)
            c = caw(rng, length, f0 * 1.05, f0 * rng.uniform(0.55, 0.75),
                    [(550, 140, 1.0), (1150, 220, 0.8), (1900, 300, 0.4)], 0.6, 0.3)
            tt = seconds(0.08)       # a hollow knock at the start: "kronk"
            c[: len(tt)] += np.sin(2 * np.pi * 420 * tt) * np.exp(-tt * 55) * 0.5
            place(out, c, at)
            at += length + rng.uniform(0.2, 0.4)
    out = lowpass(out[: int((at + 0.1) * RATE)], 6500)
    return reverb(np.concatenate([out, np.zeros(int(0.5 * RATE))]), 0.45)


# ---- The Ophion Occult Order ----

VOWELS = {
    "oh": [(500, 70, 1.0), (850, 110, 0.7), (2400, 250, 0.1)],
    "ah": [(700, 90, 1.0), (1100, 130, 0.8), (2500, 250, 0.12)],
    "oo": [(300, 60, 1.0), (800, 100, 0.5), (2300, 250, 0.06)],
}


def chant():
    rng = np.random.default_rng(4790)
    seg, nseg = 4.0, 4
    length = seg * nseg
    over = int(1.0 * RATE)
    n = int(length * RATE) + over
    t = np.arange(n) / RATE
    tm = t % length
    k = np.floor(tm / seg).astype(int)
    step = smooth(0.7, 1.0, tm / seg - k)           # glide to the next note late in each segment
    notes = [[98.0, 110.0, 98.0, 87.3], [123.5, 130.8, 123.5, 110.0], [73.4, 82.4, 73.4, 65.4]]
    vseq = ["oh", "ah", "oo", "ah"]
    mix = np.zeros(n)
    for v, (seq, det) in enumerate(zip(notes, [1.0, 1.004, 0.996])):
        a = np.array(seq)
        f0 = (a[k] * (1 - step) + a[(k + 1) % nseg] * step) * det
        f0 = f0 * (1 + 0.006 * np.sin(2 * np.pi * (4.7 + 0.5 * v) * t + v) + 0.004 * np.sin(2 * np.pi * 0.25 * t * (v + 1)))
        voice = np.zeros(n)
        tv = (tm + 0.5 * v) % length      # the voices change vowel at slightly different moments
        kv = np.floor(tv / seg).astype(int)
        sv = smooth(0.6, 0.95, tv / seg - kv)
        for name in VOWELS:
            cur = np.array([vseq[i] == name for i in range(nseg)], float)
            nxt = np.array([vseq[(i + 1) % nseg] == name for i in range(nseg)], float)
            w = cur[kv] * (1 - sv) + nxt[kv] * sv
            if w.max() > 0:
                voice += w * vowel(t, f0, VOWELS[name], 0.08, rng)
        voice *= 0.75 + 0.25 * np.sin(2 * np.pi * t / 8 + v * 2)
        mix += voice / max(1e-9, np.std(voice))
    mix = lowpass(mix, 1300)       # heard through trees
    return loopify(mix, int(length * RATE), over)


def murmur(seed):
    rng = np.random.default_rng(4800 + seed)
    length = [2.2, 2.7, 3.0][seed - 1]
    out = np.zeros(int((length + 0.2) * RATE))
    at = 0.05
    base = rng.uniform(95, 125)
    while at < length - 0.2:
        d = rng.uniform(0.11, 0.24)
        if rng.random() < 0.12:
            at += rng.uniform(0.15, 0.3)     # a pause between words
            continue
        t = seconds(d)
        f1 = rng.uniform(380, 800)
        f2 = rng.uniform(900, 2200)
        f0 = base * (1 + 0.1 * np.sin(np.pi * at / length * 3)) * (1 - 0.1 * t / d) * rng.uniform(0.95, 1.08)
        syl = vowel(t, f0, [(f1, 80, 1.0), (f2, 160, 0.5), (2800, 300, 0.1)], 0.6, rng)
        syl /= max(1e-9, np.max(np.abs(syl)))
        env = smooth(0, 0.3 * d, t) * (1 - smooth(0.6 * d, d, t))
        cons = band(rng.normal(size=len(t)), rng.uniform(800, 2500), rng.uniform(4000, 7000)) * np.exp(-t * 90)
        cons *= rng.uniform(0.2, 0.6) / max(1e-9, np.max(np.abs(cons)))
        place(out, (syl * env + cons) * rng.uniform(0.6, 1.0), at)
        at += d * rng.uniform(0.8, 1.0)
    out = band(out, 100, 3500)
    return reverb(out, 0.25)


# ---- The forest ----

def shift(seed):
    rng = np.random.default_rng(4820 + seed)
    length = [1.8, 2.4][seed - 1]
    out = np.zeros(int(length * RATE))
    hit = 0.8 + 0.3 * (seed - 1)
    sw = seconds(hit - 0.1)       # a reversed swell before it
    swell = band(rng.normal(size=len(sw)), 300, 2500)
    swell *= (sw / sw[-1]) ** 3 * 0.35 / np.std(swell)
    place(out, swell * 0.3, 0.05)
    wt = seconds(0.9)             # the whump of air
    whump = np.sin(2 * np.pi * np.cumsum(55 * (1 - 0.4 * wt / 0.9)) / RATE) * np.exp(-wt * 5) * smooth(0, 0.03, wt)
    low = band(rng.normal(size=len(wt)), 30, 280)
    whump += low / np.std(low) * np.exp(-wt * 6) * 0.3
    place(out, whump, hit)
    rt = seconds(length - hit - 0.1)    # leaves rustling after
    rustle = np.zeros(len(rt))
    for _ in range(int(rt[-1] * 90)):
        at = rng.uniform(0, rt[-1] - 0.03)
        w = int(rng.uniform(0.005, 0.02) * RATE)
        k = np.arange(w) / RATE
        g = band(rng.normal(size=w + 64), rng.uniform(1500, 3500), rng.uniform(5000, 10000))[:w] * np.exp(-k * 300)
        place(rustle, g * rng.uniform(0.1, 0.5) * np.exp(-at * 1.8) / 0.2, int(at * RATE) / RATE)
    place(out, rustle / max(1e-9, np.max(np.abs(rustle))) * 0.12, hit + 0.15)
    return lowpass(out, 7000)


def branchsnap(seed):
    rng = np.random.default_rng(4830 + seed)
    length = [0.5, 0.75][seed - 1]
    out = np.zeros(int(length * RATE))
    at = 0.03 if seed == 1 else 0.28
    if seed == 2:
        ct = seconds(0.26)
        creak = band(rng.normal(size=len(ct)), 300, 1400) * (0.5 + 0.5 * np.sin(2 * np.pi * 45 * ct * (1 + ct))) * smooth(0, 0.2, ct)
        place(out, creak / np.max(np.abs(creak)) * 0.25, 0.0)
    t = seconds(0.16)
    crack = band(rng.normal(size=len(t)), 1200, 9000) * np.exp(-t * 130)
    crack /= np.max(np.abs(crack))
    ring = np.sin(2 * np.pi * 900 * t) * np.exp(-t * 90) * 0.4 + np.sin(2 * np.pi * 1700 * t) * np.exp(-t * 130) * 0.2
    place(out, crack + ring, at)
    for i in range(3 + seed):         # splinters
        w = seconds(0.03)
        s = band(rng.normal(size=len(w) + 32), 1500, 7000)[: len(w)] * np.exp(-w * 150)
        place(out, s / np.max(np.abs(s)) * rng.uniform(0.15, 0.4), at + rng.uniform(0.04, 0.25))
    th = seconds(0.1)
    place(out, np.sin(2 * np.pi * 120 * th) * np.exp(-th * 40) * 0.3, at + 0.14)
    return reverb(out, 0.25)


def woodpecker():
    rng = np.random.default_rng(4850)
    out = np.zeros(int(1.5 * RATE))
    at = 0.05
    while at < 1.35:
        rate = 21 - 12 * (at / 1.5) ** 1.3
        t = seconds(0.04)
        f = rng.uniform(1700, 2000)
        noise = band(rng.normal(size=len(t)), 800, 4000)
        knock = np.sin(2 * np.pi * f * t) * np.exp(-t * 220) + noise / np.std(noise) * np.exp(-t * 250) * 0.3
        place(out, knock * (1 - 0.35 * at / 1.5) * rng.uniform(0.8, 1.0), at)
        at += (1 / rate) * rng.uniform(0.94, 1.06)
    return reverb(lowpass(out, 4500), 0.5)


def main():
    for i in (1, 2, 3):
        write("creature", "snakehiss%d" % i, snake_hiss(i), 0.55)
    for i in (1, 2):
        write("creature", "adderhiss%d" % i, adder_hiss(i), 0.85)
    write("creature", "adderroar", adder_roar(), 0.85)
    write("creature", "adderstrike", adder_strike(), 0.9)
    write("creature", "adderslither", adder_slither(), 0.7, fade=False)
    write("creature", "adderswallow", adder_swallow(), 0.85)
    for i in (1, 2, 3, 4):
        write("ambient", "crow%d" % i, bird_take(i, "crow"), 0.6)
    for i in (1, 2, 3):
        write("ambient", "raven%d" % i, bird_take(i, "raven"), 0.65)
    write("ambient", "chant", chant(), 0.6, fade=False)
    for i in (1, 2, 3):
        write("ambient", "murmur%d" % i, murmur(i), 0.5)
    for i in (1, 2):
        write("ambient", "shift%d" % i, shift(i), 0.55)
        write("ambient", "branchsnap%d" % i, branchsnap(i), 0.75)
    write("ambient", "woodpecker", woodpecker(), 0.5)


if __name__ == "__main__":
    main()
