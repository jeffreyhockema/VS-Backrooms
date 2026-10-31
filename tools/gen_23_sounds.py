"""Synthesises the sounds of Level 23, "The Petrified Garden" (experimental): the Gardener's Sorries whispering "sorry"
(three takes: one voice, a quicker one, and several at once), a buried sentry's scream (a rusty chainsaw cutting wood,
with something like a voice in it), and the deep groan of the petrified trees.

Run from the repo root under the asset lock:  bash tools/locked.sh run python tools/gen_23_sounds.py
Writes assets/backrooms/sounds/ambient/23/*.ogg.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from oggutil import write_ogg  # noqa: E402

from gen_entity_sounds import RATE, band, place, reverb, seconds, vowel  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "assets", "backrooms", "sounds", "ambient", "23")


def write(name, signal, peak):
    path = os.path.join(OUT, name + ".ogg")
    signal = np.asarray(signal, dtype=np.float64)
    n = min(len(signal) // 4, int(0.01 * RATE))
    if n > 0:
        signal[:n] *= np.linspace(0, 1, n)
        signal[-n:] *= np.linspace(1, 0, n)
    signal = peak * signal / max(1e-9, np.max(np.abs(signal)))
    if write_ogg(path, signal, RATE):
        print("wrote", os.path.relpath(path, ROOT))


# ---- A whisper: noise through moving formants, frame by frame ----

# "sorry": the keyframes (time in s; formants as (frequency, bandwidth, gain); loudness; how much of it is the hiss of an s)
SORRY = [
    (0.00, [(5200, 1600, 1.0)], 0.0, 1.0),
    (0.06, [(5600, 1800, 1.0)], 0.55, 1.0),
    (0.15, [(5600, 1800, 1.0)], 0.5, 1.0),
    (0.19, [(650, 130, 1.0), (1000, 150, 0.8), (2600, 260, 0.35)], 1.0, 0.0),
    (0.30, [(620, 130, 1.0), (980, 150, 0.8), (2500, 260, 0.3)], 0.95, 0.0),
    (0.37, [(460, 110, 1.0), (1150, 160, 0.7), (1550, 200, 0.45)], 0.8, 0.0),
    (0.44, [(320, 90, 1.0), (2200, 220, 0.7), (2950, 280, 0.4)], 0.85, 0.0),
    (0.58, [(300, 90, 1.0), (2300, 230, 0.6), (3000, 280, 0.35)], 0.5, 0.0),
    (0.68, [(300, 90, 1.0), (2300, 230, 0.5), (3000, 280, 0.3)], 0.0, 0.0),
]


def _key(t):
    """The formants, loudness and hiss at time t, eased between the keyframes."""
    for (t0, f0, a0, s0), (t1, f1, a1, s1) in zip(SORRY, SORRY[1:]):
        if t0 <= t <= t1:
            u = (t - t0) / max(1e-6, t1 - t0)
            u = u * u * (3 - 2 * u)
            if len(f0) == len(f1):
                f = [(a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u) for a, b in zip(f0, f1)]
            else:
                f = f0 if u < 0.5 else f1
            return f, a0 + (a1 - a0) * u, s0 + (s1 - s0) * u
    return SORRY[-1][1], 0.0, 0.0


def whisper_sorry(rng, speed=1.0, size=1.0, breath=0.25):
    """One whispered "sorry": white noise shaped by the moving formants (scaled by the voice's size), overlap-added."""
    length = SORRY[-1][0] / speed
    n = int((length + 0.05) * RATE)
    out = np.zeros(n)
    frame, hop = 1024, 256
    win = np.hanning(frame)
    freqs = np.fft.rfftfreq(frame, 1 / RATE)
    for start in range(0, n - frame, hop):
        t = (start + frame / 2) / RATE * speed
        formants, loud, hiss = _key(t)
        if loud <= 0.001:
            continue
        noise = rng.normal(size=frame)
        spec = np.fft.rfft(noise)
        shape = np.zeros_like(freqs)
        for fc, bw, g in formants:
            fc = fc * (size if fc < 4000 else 1)
            shape += g * np.exp(-((freqs - fc) / bw) ** 2)
        shape = (1 - hiss) * shape + hiss * shape
        shape += breath * 0.08 * np.exp(-((freqs - 1800) / 2500) ** 2)
        frm = np.fft.irfft(spec * shape, n=frame) * win * loud
        out[start:start + frame] += frm
    return band(out, 180, 9000)


def cave(signal, wet=0.35):
    """A cavern: the hallway reverb with a longer, darker tail."""
    r = reverb(signal, decay=0.55)
    return (1 - wet) * signal + wet * r


def sorries():
    rng = np.random.default_rng(2301)
    # One voice, slow and soft
    one = np.zeros(int(1.4 * RATE))
    place(one, whisper_sorry(rng, 0.85, 1.0), 0.1)
    write("sorry1", cave(one), 0.5)
    # A smaller voice, quicker, saying it twice
    two = np.zeros(int(1.8 * RATE))
    place(two, whisper_sorry(rng, 1.15, 1.18), 0.05)
    place(two, 0.8 * whisper_sorry(rng, 1.1, 1.18), 0.75)
    write("sorry2", cave(two), 0.45)
    # Many at once, overlapping, some further off
    many = np.zeros(int(2.4 * RATE))
    for k in range(6):
        w = whisper_sorry(rng, rng.uniform(0.85, 1.2), rng.uniform(0.9, 1.25))
        far = rng.uniform(0.35, 1.0)
        if far < 0.6:
            w = band(w, 200, 4000)
        place(many, far * w, rng.uniform(0, 1.5))
    write("sorry3", cave(many, 0.5), 0.45)


# ---- A buried sentry's scream ----

def sentryscream():
    """A rusty chainsaw through wood: a buzzing saw tone chattering with its teeth, chips cracking, and in it something
    like a voice screaming; rising, then choking off."""
    rng = np.random.default_rng(2310)
    t = seconds(2.6)
    n = len(t)
    env = np.minimum(1, t / 0.08) * np.clip((2.6 - t) / 0.5, 0, 1)
    # The saw: a sawtooth, its pitch climbing, chattering at the teeth's rate
    f0 = 95 + 45 * np.minimum(1, t / 1.6) + 6 * np.sin(2 * np.pi * 3.1 * t)
    phase = np.cumsum(f0) / RATE
    saw = 2 * (phase % 1) - 1
    teeth = 0.55 + 0.45 * np.sign(np.sin(2 * np.pi * 31 * t + 2 * np.sin(2 * np.pi * 0.7 * t)))
    body = band(saw * teeth, 60, 5000)
    # Chips: rough noise in a band, gated by the chain
    chips = band(rng.normal(size=n), 900, 6000) * (0.5 + 0.5 * np.sin(2 * np.pi * 93 * t) ** 8)
    # The voice in it: a screamed "aah", jittering, pushed past breaking
    fv = (420 + 160 * np.minimum(1, t / 1.2)) * (1 + 0.04 * rng.normal(size=n).cumsum() / np.sqrt(np.arange(1, n + 1)))
    voice = vowel(t, fv, ((850, 160, 1.0), (1300, 200, 0.8), (2900, 300, 0.5)), breath=0.5, rng=rng)
    voice *= np.clip((t - 0.15) / 0.3, 0, 1)
    mix = 0.9 * body / np.max(np.abs(body)) + 0.5 * chips / np.max(np.abs(chips)) + 0.75 * voice / np.max(np.abs(voice))
    mix = np.tanh(2.6 * mix) * env
    # Cracks of the wood giving
    for _ in range(14):
        at = rng.uniform(0.1, 2.3)
        k = seconds(0.03)
        place(mix, 0.6 * band(rng.normal(size=len(k)), 500, 7000) * np.exp(-k * 120), at)
    write("sentryscream", reverb(mix, 0.5), 0.8)


# ---- The trees groaning ----

def woodgroan():
    """Wood under strain: slow stick-slip clicks through the resonances of a great trunk, and a low groan under them."""
    rng = np.random.default_rng(2320)
    t = seconds(2.8)
    n = len(t)
    out = np.zeros(n)
    at, rate = 0.15, 14.0
    while at < 2.4:
        k = seconds(0.04)
        click = rng.normal(size=len(k)) * np.exp(-k * 160)
        place(out, click * (0.5 + 0.5 * np.sin(np.pi * at / 2.4)), at)
        rate = float(np.clip(rate + rng.normal() * 3, 8, 34))
        at += 1 / rate
    spec = np.fft.rfft(out)
    f = np.fft.rfftfreq(n, 1 / RATE)
    res = sum(g * np.exp(-((f - fc) / bw) ** 2) for fc, bw, g in ((170, 30, 1.0), (410, 50, 0.7), (880, 90, 0.4), (1500, 160, 0.15)))
    creak = np.fft.irfft(spec * res, n=n)
    f0 = 58 + 10 * np.sin(np.pi * t / 2.8)
    groan = band(2 * ((np.cumsum(f0) / RATE) % 1) - 1, 40, 400) * np.sin(np.pi * np.clip(t / 2.8, 0, 1)) ** 2
    mix = creak / np.max(np.abs(creak)) + 0.45 * groan / np.max(np.abs(groan))
    write("woodgroan", reverb(mix, 0.6), 0.6)


def main():
    sorries()
    sentryscream()
    woodgroan()


if __name__ == "__main__":
    main()
