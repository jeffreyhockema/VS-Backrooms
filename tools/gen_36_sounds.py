"""Level 36, the Airport: its sounds, synthesised.

ambient/36/: hum (terminal bed), belt (baggage carousel), static (the Absolute Limit), cabin (inside a plane), service
(back-of-house ducts). All five are seamless loops (circular filtering, whole cycles, wrapped events).
effect/36/: chime1/2 (the PA chime), pa1-3 (distant unintelligible announcements), jet1/2 (take-off, landing), clunk
(carousel), ding (seatbelt sign), touchdown, boarding, pushback, takeoff (flight status pass).

Run:  bash tools/locked.sh run python tools/gen_36_sounds.py
"""
import os
import sys

import numpy as np
from oggutil import write_ogg
from gen_entity_sounds import RATE, band, place, seconds, vowel

TAU = 2 * np.pi
ROOT = os.path.join(os.path.dirname(__file__), "..")
SOUNDS = os.path.join(ROOT, "assets", "backrooms", "sounds")
STATS = []


def write(folder, name, signal, peak, loop=False):
    path = os.path.join(SOUNDS, *folder.split("/"), name + ".ogg")
    signal = np.asarray(signal, dtype=np.float64)
    if not loop:
        n = min(len(signal) // 8, int(0.008 * RATE))
        signal[:n] *= np.linspace(0, 1, n)
        signal[-n * 6:] *= np.linspace(1, 0, n * 6)
    signal = peak * signal / max(1e-9, np.max(np.abs(signal)))
    write_ogg(path, signal, RATE)
    jump = abs(signal[0] - signal[-1])
    step = float(np.std(np.diff(signal)))
    STATS.append((f"{folder}/{name}", len(signal) / RATE, float(np.max(np.abs(signal))),
                  float(np.sqrt(np.mean(signal ** 2))), jump / max(step, 1e-9) if loop else None))


# ------------------------------------------------------------------ helpers

def shape(x, fn):
    """Circular spectral shaping: fn(f) gives the gain at each frequency."""
    s = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / RATE)
    return np.fft.irfft(s * fn(f), n=len(x))


def lp(x, fc, order=4):
    return shape(x, lambda f: 1 / (1 + (f / fc) ** order))


def pink(n, rng):
    return shape(rng.normal(size=n), lambda f: 1 / np.sqrt(np.maximum(f, 20)))


def slow(n, rng, rate, lo=0.0, hi=1.0):
    """A slow random envelope (circular), values in lo..hi, wandering about `rate` Hz."""
    x = lp(rng.normal(size=n), rate, 2)
    x = (x - x.min()) / (x.max() - x.min())
    return lo + (hi - lo) * x


def cyc(f, dur):
    """A frequency rounded to whole cycles in `dur` seconds (so a tone loops seamlessly)."""
    return max(1, round(f * dur)) / dur


def wrap_add(out, sound, at):
    i = int(at * RATE) % len(out)
    n = len(sound)
    first = min(n, len(out) - i)
    out[i:i + first] += sound[:first]
    rest = n - first
    while rest > 0:
        k = min(rest, len(out))
        out[:k] += sound[first:first + k]
        first += k
        rest -= k


def env(n, attack, release):
    e = np.ones(n)
    a, r = int(attack * RATE), int(release * RATE)
    if a > 0:
        e[:min(a, n)] = np.linspace(0, 1, min(a, n))
    if r > 0:
        e[max(0, n - r):] *= np.linspace(1, 0, n - max(0, n - r))
    return e


def hall(x, rt=2.0, wet=0.5, tail=None, seed=11, dark=3500):
    """A large hall: an exponentially decaying filtered-noise impulse response (FFT convolution)."""
    tail = rt * 1.2 if tail is None else tail
    n = len(x) + int(tail * RATE)
    r = np.random.default_rng(seed)
    m = int(rt * 1.3 * RATE)
    t = np.arange(m) / RATE
    ir = r.normal(size=m) * np.exp(-t * 6.9 / rt)
    ir = lp(ir, dark, 2)
    k = int(0.02 * RATE)
    ir[:k] *= np.linspace(0, 1, k)
    ir /= np.sqrt(np.sum(ir ** 2))
    size = 1 << int(np.ceil(np.log2(n + m)))
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[:n]
    dry = np.zeros(n)
    dry[:len(x)] = x
    return (1 - wet) * dry + wet * y * np.std(x) / max(np.std(y), 1e-9) * 0.8


def bell(f, dur, decay=4.0, parts=((1, 1.0), (2.0, 0.25), (3.0, 0.08), (2.76, 0.1))):
    t = seconds(dur)
    s = sum(a * np.sin(TAU * f * k * t) * np.exp(-t * decay * (0.6 + 0.4 * k)) for k, a in parts)
    return s * env(len(t), 0.006, 0.04)


# ------------------------------------------------------------------ ambient loops

def ambients():
    # --- hum: HVAC rumble + hiss, 120 Hz fluorescent buzz, a far crowd that is not there (30 s)
    D = 30
    n = D * RATE
    rng = np.random.default_rng(3601)
    t = np.arange(n) / RATE
    rumble = lp(pink(n, rng), 160, 2)
    rumble /= np.std(rumble)
    air = band(rng.normal(size=n), 400, 5000)
    air = lp(air, 2500, 2) / np.std(air)
    air *= 0.6 + 0.4 * slow(n, rng, 0.15)
    buzz = sum(a * np.sin(TAU * cyc(f, D) * t + p) for f, a, p in ((120, 1.0, 0), (240, 0.4, 1.1), (360, 0.22, 2.0), (480, 0.1, 0.4)))
    buzz = buzz * (1 + 0.08 * np.sin(TAU * t / 10 * 3))
    murm = band(rng.normal(size=n), 180, 1400)
    murm = lp(murm, 900, 2)
    syl = np.zeros(n)
    for hz_, w in ((3.1, 1.0), (4.7, 0.7), (1.3, 0.5)):
        s = lp(rng.normal(size=n), hz_, 2)
        syl += w * s / np.std(s)
    syl = 0.5 + 0.5 * np.tanh(syl)
    murm = murm / np.std(murm) * syl * (0.3 + 0.7 * slow(n, rng, 0.07))
    mix = 1.0 * rumble + 0.28 * air + 0.045 * buzz + 0.07 * murm
    write("ambient/36", "hum", mix, 0.30, loop=True)

    # --- belt: carousel, 16 s loop
    D = 16
    n = D * RATE
    rng = np.random.default_rng(3602)
    t = np.arange(n) / RATE
    motor = sum(a * np.sin(TAU * cyc(f, D) * t) for f, a in ((50, 1.0), (100, 0.5), (150, 0.15))) * (1 + 0.1 * np.sin(TAU * t / 8))
    rolls = lp(band(rng.normal(size=n), 80, 900), 500, 2)
    rolls /= np.std(rolls)
    whine = np.sin(TAU * cyc(930, D) * t + 0.8 * np.sin(TAU * 4 * t / D)) + 0.4 * np.sin(TAU * cyc(1395, D) * t)
    whine = whine * (0.5 + 0.5 * slow(n, rng, 0.2))
    out = 0.12 * motor + 0.1 * rolls + 0.012 * whine
    period = 1.6  # a slat plate passes the joint
    for k in range(int(D / period)):
        at = 0.5 + k * period
        tc = seconds(0.12)
        clack = band(rng.normal(size=len(tc)), 500, 3500) * np.exp(-tc * 70)
        clack += 0.7 * np.sin(TAU * 150 * tc) * np.exp(-tc * 45)
        clack2 = band(rng.normal(size=len(tc)), 300, 2500) * np.exp(-tc * 55)
        wrap_add(out, clack * 0.5 * (1 + 0.15 * rng.normal()), at)
        wrap_add(out, clack2 * 0.3, at + 0.17)
        tr = seconds(0.5)
        wrap_add(out, lp(rng.normal(size=len(tr)), 200, 2) * np.sin(np.pi * tr / tr[-1]) ** 2 * 0.15, at - 0.1)
    write("ambient/36", "belt", out, 0.22, loop=True)

    # --- static: the Absolute Limit (20 s)
    D = 20
    n = D * RATE
    rng = np.random.default_rng(3603)
    t = np.arange(n) / RATE
    white = shape(rng.normal(size=n), lambda f: 1 / (1 + (f / 9000) ** 4))
    swell = 0.45 + 0.55 * np.sin(TAU * t / D * 2 + 0.7) ** 2 * (0.6 + 0.4 * slow(n, rng, 0.3))
    hiss = white * swell
    low = lp(rng.normal(size=n), 400, 2) * 0.5 * (1 - swell)
    gate = np.clip((slow(n, rng, 0.12) - 0.55) * 4, 0, 1)
    tone = (np.sin(TAU * cyc(440, D) * t) + 0.9 * np.sin(TAU * cyc(446.5, D) * t) + 0.3 * np.sin(TAU * cyc(883, D) * t)) * gate
    crack = np.zeros(n)
    for _ in range(60):
        tc = seconds(rng.uniform(0.002, 0.02))
        wrap_add(crack, band(rng.normal(size=len(tc)), 1500, 12000) * np.exp(-tc / tc[-1] * 5) * rng.uniform(0.5, 3), rng.uniform(0, D))
    out = hiss + low + 0.10 * tone * np.std(white) + 0.25 * crack * np.std(white)
    write("ambient/36", "static", out, 0.30, loop=True)

    # --- cabin: jet cabin roar (30 s)
    D = 30
    n = D * RATE
    rng = np.random.default_rng(3604)
    t = np.arange(n) / RATE
    roar = lp(pink(n, rng), 1800, 2)
    roar /= np.std(roar)
    roar = roar * (0.85 + 0.15 * slow(n, rng, 0.2))
    drone = sum(a * np.sin(TAU * cyc(f, D) * t + p) for f, a, p in ((88, 1.0, 0), (91.0, 0.9, 1), (176, 0.35, 2), (181.7, 0.3, 3), (264, 0.12, 0.5)))
    drone = drone * (1 + 0.1 * np.sin(TAU * t / 10))
    vent = band(rng.normal(size=n), 3500, 9000)
    vent = vent / np.std(vent) * (0.5 + 0.5 * slow(n, rng, 0.1))
    out = 1.0 * roar + 0.2 * drone / np.std(drone) + 0.16 * vent
    write("ambient/36", "cabin", out, 0.30, loop=True)

    # --- service: ducts and fans (24 s)
    D = 24
    n = D * RATE
    rng = np.random.default_rng(3605)
    t = np.arange(n) / RATE
    duct = lp(pink(n, rng), 220, 3)
    duct /= np.std(duct)
    duct = duct * (0.8 + 0.2 * slow(n, rng, 0.1))
    blade = band(rng.normal(size=n), 60, 500)
    blade = blade / np.std(blade) * (0.55 + 0.45 * np.sin(TAU * cyc(32, D) * t))
    fan = np.sin(TAU * cyc(32, D) * t) * 0.4 + np.sin(TAU * cyc(64, D) * t + 1) * 0.2 + np.sin(TAU * cyc(48.5, D) * t) * 0.15
    air = lp(band(rng.normal(size=n), 700, 4000), 2000, 2)
    air = air / np.std(air) * 0.1 * (0.5 + 0.5 * slow(n, rng, 0.12))
    out = 1.0 * duct + 0.45 * blade + 0.5 * fan + air
    for _ in range(7):
        f0 = rng.uniform(900, 2600)
        tt = seconds(0.6)
        tick = (np.sin(TAU * f0 * tt) + 0.5 * np.sin(TAU * f0 * 2.43 * tt)) * np.exp(-tt * rng.uniform(25, 60))
        tick = lp(tick, 3500, 2)
        at = rng.uniform(0, D)
        wrap_add(out, tick * 0.12, at)
        wrap_add(out, tick * 0.04, at + 0.23)
    write("ambient/36", "service", out, 0.30, loop=True)


# ------------------------------------------------------------------ voices

VOWELS = [[(700, 90, 1.0), (1200, 120, 0.6), (2600, 200, 0.2)], [(400, 70, 1.0), (2000, 150, 0.5), (2700, 200, 0.25)],
          [(500, 80, 1.0), (900, 100, 0.6), (2400, 200, 0.2)], [(300, 60, 1.0), (2300, 150, 0.4), (3000, 200, 0.2)],
          [(600, 90, 1.0), (1700, 140, 0.5), (2500, 200, 0.2)], [(350, 60, 1.0), (800, 90, 0.6), (2500, 200, 0.15)]]


def babble(seed, phrases, f0=160.0):
    """Speech-like babble, no words: syllables of a steady pitch with moving vowels, phrase pauses. phrases: syllable counts."""
    rng = np.random.default_rng(seed)
    out = np.zeros(int(14 * RATE))
    at = 0.25
    for count in phrases:
        for k in range(count):
            dur = rng.uniform(0.11, 0.24)
            ts = seconds(dur)
            drift = 1 + 0.025 * np.sin(np.pi * k / max(1, count - 1)) - 0.02 * k / max(1, count)
            pitch = f0 * drift * (1 + 0.012 * np.sin(TAU * 4.5 * ts))
            v1, v2 = VOWELS[rng.integers(0, len(VOWELS))], VOWELS[rng.integers(0, len(VOWELS))]
            h = len(ts) // 2
            syl = np.concatenate([vowel(ts[:h], pitch[:h], v1, 0.04, rng), vowel(ts[h:], pitch[h:], v2, 0.04, rng)])
            syl = syl / (np.max(np.abs(syl)) + 1e-9) * np.sin(np.pi * np.arange(len(syl)) / len(syl)) ** 1.2
            if rng.random() < 0.35:  # a sibilant onset
                tn = seconds(0.06)
                syl = np.concatenate([band(rng.normal(size=len(tn)), 3000, 7000) * 0.25 * np.sin(np.pi * tn / tn[-1]), syl])
            place(out, syl, at)
            at += len(syl) / RATE + rng.uniform(0.0, 0.05)
            if rng.random() < 0.18:
                at += rng.uniform(0.12, 0.22)  # a word gap
        at += rng.uniform(0.5, 0.9)
    return out[:int((at + 0.2) * RATE)]


def pa_speaker(x):
    x = band(x, 300, 3500)
    x = np.tanh(2.0 * x / (np.std(x) + 1e-9)) * np.std(x)
    return band(x, 300, 3400)


# ------------------------------------------------------------------ effects

def chimes():
    for name, notes, gap in (("chime1", (659.3, 784.0, 987.8), 0.5), ("chime2", (523.3, 698.5, 880.0), 0.55)):
        out = np.zeros(int(2.0 * RATE))
        for k, f in enumerate(notes):
            place(out, bell(f, 1.6, 3.2) * (0.8 + 0.2 * k), k * gap)
        write("effect/36", name, hall(out, 1.6, 0.4, tail=0.6), 0.45)


def pas():
    for i, phr in enumerate(((5, 6, 4), (5, 4, 4), (4, 7)), 1):
        dry = babble(3610 + i, phr, 150 + 8 * i)
        sig = hall(pa_speaker(dry), 2.8, 0.55, tail=1.2, seed=20 + i)
        write("effect/36", f"pa{i}", lp(sig, 3200, 2), 0.40)


def jets():
    rng = np.random.default_rng(3620)
    # take-off: slow swell, whine climbing, then fading away; heavily muffled
    n = 16 * RATE
    t = np.arange(n) / RATE
    swell = np.exp(-((t - 6.5) / 3.6) ** 2)
    roar = lp(pink(n, rng), 650, 3)
    roar /= np.std(roar)
    f = 500 + 450 * np.clip(t / 7, 0, 1)
    whine = np.sin(TAU * np.cumsum(f) / RATE) + 0.4 * np.sin(TAU * np.cumsum(f * 2.01) / RATE)
    out = (roar * swell * (0.5 + 0.5 * swell)) + 0.08 * lp(whine, 1100, 3) * np.exp(-((t - 5.5) / 3.0) ** 2)
    out = lp(out, 900, 3)
    write("effect/36", "jet1", hall(out, 2.2, 0.35, tail=1.0, seed=31), 0.40)
    # landing: whine coming in, touch, reverse-thrust roar, fading
    n = 16 * RATE
    t = np.arange(n) / RATE
    f = 1100 - 450 * np.clip(t / 8, 0, 1)
    whine = np.sin(TAU * np.cumsum(f) / RATE) + 0.4 * np.sin(TAU * np.cumsum(f * 1.5) / RATE)
    pre = lp(pink(n, rng), 700, 3)
    pre /= np.std(pre)
    out = 0.07 * lp(whine, 1300, 3) * np.exp(-((t - 5.0) / 2.4) ** 2) + 0.4 * pre * np.exp(-((t - 5) / 2.0) ** 2)
    thump = np.zeros(n)
    tt = seconds(0.6)
    place(thump, (np.sin(TAU * 45 * tt * (1 - 0.3 * tt)) * np.exp(-tt * 9)) * 0.6, 6.0)
    rev = lp(pink(n, rng), 800, 3)
    rev /= np.std(rev)
    renv = np.clip((t - 6.3) / 1.0, 0, 1) * np.exp(-np.clip(t - 7.0, 0, None) / 2.3)
    out = lp(out + thump + 1.0 * rev * renv, 950, 3)
    write("effect/36", "jet2", hall(out, 2.2, 0.35, tail=1.0, seed=32), 0.40)


def mech():
    rng = np.random.default_rng(3630)
    # clunk: heavy clunk, then a short motor wind
    out = np.zeros(int(2.2 * RATE))
    tt = seconds(0.5)
    clunk = np.sin(TAU * 62 * tt * (1 - 0.2 * tt)) * np.exp(-tt * 11) + 0.6 * band(rng.normal(size=len(tt)), 150, 2200) * np.exp(-tt * 38)
    clunk += 0.25 * (np.sin(TAU * 410 * tt) + 0.5 * np.sin(TAU * 1130 * tt)) * np.exp(-tt * 30)
    place(out, clunk, 0.05)
    tw = seconds(1.3)
    f = 35 + 85 * (1 - np.exp(-tw * 2.5))
    wind = np.sin(TAU * np.cumsum(f) / RATE) + 0.5 * np.sin(TAU * np.cumsum(2 * f) / RATE) + 0.2 * np.sin(TAU * np.cumsum(3 * f) / RATE)
    wind = wind * env(len(tw), 0.2, 0.5) * 0.28
    wind += 0.1 * band(rng.normal(size=len(tw)), 200, 1500) * env(len(tw), 0.2, 0.5)
    place(out, wind, 0.25)
    write("effect/36", "clunk", hall(out, 0.7, 0.2, tail=0.1), 0.5)
    # ding: the seatbelt sign
    out = np.zeros(int(1.5 * RATE))
    place(out, bell(1318.5, 1.3, 3.0, ((1, 1.0), (2.0, 0.12), (3.0, 0.04))), 0.0)
    place(out, 0.85 * bell(987.8, 1.2, 3.2, ((1, 1.0), (2.0, 0.12), (3.0, 0.04))), 0.28)
    write("effect/36", "ding", hall(out, 0.8, 0.2, tail=0.1), 0.45)
    # touchdown: thump, squeal hint, reverse-thrust roar swelling and dying
    n = int(6.2 * RATE)
    t = np.arange(n) / RATE
    out = np.zeros(n)
    for at, a in ((0.25, 1.0), (0.55, 0.65)):
        tt = seconds(0.5)
        place(out, a * (np.sin(TAU * 50 * tt * (1 - 0.3 * tt)) * np.exp(-tt * 10) + 0.5 * band(rng.normal(size=len(tt)), 80, 1200) * np.exp(-tt * 30)), at)
    tq = seconds(0.7)
    sq = band(rng.normal(size=len(tq)), 1800, 3200) * (0.5 + 0.5 * np.sin(TAU * 11 * tq)) * np.sin(np.pi * tq / tq[-1]) ** 2
    sq += 0.4 * np.sin(TAU * np.cumsum(1900 + 400 * tq / tq[-1]) / RATE) * np.sin(np.pi * tq / tq[-1]) ** 2
    place(out, sq * 0.22, 0.25)
    roar = lp(pink(n, rng), 1100, 3)
    roar /= np.std(roar)
    renv = np.clip((t - 0.9) / 1.4, 0, 1) ** 1.5 * np.exp(-np.clip(t - 2.8, 0, None) / 1.3)
    out += 0.55 * roar * renv
    write("effect/36", "touchdown", out, 0.5)
    # boarding: chime, then a muffled babble
    out = np.zeros(int(5.0 * RATE))
    for k, f in enumerate((587.3, 740.0, 880.0)):
        place(out, bell(f, 1.5, 3.4) * (0.8 + 0.2 * k), k * 0.45)
    voice = lp(pa_speaker(babble(3640, (5, 7), 158)), 2000, 2)[:int(3.0 * RATE)]
    place(out, voice / (np.max(np.abs(voice)) + 1e-9) * 0.35 * np.max(np.abs(out)), 1.9)
    write("effect/36", "boarding", hall(out, 2.0, 0.45, tail=0.5, seed=41)[:int(5.2 * RATE)], 0.42)


def flight():
    """(Flight status pass) pushback: the tug's low diesel rumble, a clank at the start and a lurch at the end (7 s);
    takeoff: the engines spool up, the roll rises to a full roar, the wheels leave, the roar settles to cruise (16 s)."""
    rng = np.random.default_rng(3650)
    n = int(7 * RATE)
    t = np.arange(n) / RATE
    rumble = lp(pink(n, rng), 140, 3)
    rumble /= np.std(rumble)
    f = 38 + 5 * np.sin(TAU * 0.7 * t)
    diesel = np.sin(TAU * np.cumsum(f) / RATE) + 0.6 * np.sin(TAU * np.cumsum(2 * f) / RATE) + 0.3 * np.sin(TAU * np.cumsum(3.02 * f) / RATE)
    diesel *= 0.7 + 0.3 * np.sin(TAU * 9 * t)
    out = (0.8 * rumble + 0.5 * diesel / np.std(diesel)) * np.clip(t / 0.6, 0, 1) * np.clip((7 - t) / 1.2, 0, 1)
    for at in (0.1, 6.2):
        tt = seconds(0.4)
        place(out, 1.4 * (np.sin(TAU * 70 * tt * (1 - 0.3 * tt)) * np.exp(-tt * 12) + 0.4 * band(rng.normal(size=len(tt)), 120, 1800) * np.exp(-tt * 30)), at)
    write("effect/36", "pushback", hall(lp(out, 600, 3), 0.9, 0.2, tail=0.2), 0.5)
    n = int(16 * RATE)
    t = np.arange(n) / RATE
    spool = np.clip(t / 5.0, 0, 1) ** 1.6
    f = 180 + 520 * spool
    whine = np.sin(TAU * np.cumsum(f) / RATE) + 0.45 * np.sin(TAU * np.cumsum(f * 2.01) / RATE) + 0.2 * np.sin(TAU * np.cumsum(f * 3.03) / RATE)
    roar = lp(pink(n, rng), 1500, 2)
    roar /= np.std(roar)
    level = (0.15 + 0.85 * spool) * np.where(t < 11.5, 1.0, np.exp(-(t - 11.5) / 3.0) * 0.5 + 0.5)
    rolling = 0.25 * band(rng.normal(size=n), 40, 220) / 0.3 * np.clip((t - 4) / 2, 0, 1) * np.clip((9.5 - t) / 0.6, 0, 1)
    out = level * (roar + 0.10 * whine / np.std(whine) * spool) + rolling
    tt = seconds(0.5)
    place(out, 0.9 * np.sin(TAU * 55 * tt * (1 - 0.3 * tt)) * np.exp(-tt * 9), 9.5)  # the wheels leave: a last thump
    write("effect/36", "takeoff", hall(lp(out, 1600, 2), 1.4, 0.25, tail=0.5), 0.5)


def main():
    if sys.argv[1:] == ["flight"]:
        flight()
        for name, d, pk, rms, seam in STATS:
            print(f"{name:28s} {d:6.2f} {pk:6.3f} {rms:6.3f}")
        return
    ambients()
    chimes()
    pas()
    jets()
    mech()
    flight()
    print(f"{'file':28s} {'sec':>6s} {'peak':>6s} {'rms':>6s}  seam(jump/std-step)")
    for name, d, pk, rms, seam in STATS:
        print(f"{name:28s} {d:6.2f} {pk:6.3f} {rms:6.3f}  {'' if seam is None else round(seam, 2)}")


if __name__ == "__main__":
    main()
