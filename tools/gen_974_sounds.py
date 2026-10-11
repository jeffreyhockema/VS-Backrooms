"""Level 974, Kitty's House: its sounds (sounds/ambient/974/, sounds/creature/974/). Called from gen_974.py.

A music box playing Brahms' Wiegenlied (public domain) from the bedroom, faint and muffled; the same tune warped
(slowed, flat, wavering, a note now and then missing) once the pink stops being kind; the fridge's hum; the house
creaking; an original four-note start-up chime and a "new mail" ding for the old computer; a celesta falling
asleep; a relay clunk when the lights go out. Kitty: a cloth whisper, a soft purr, a long breath out.
Written in quarter-second chunks (libsndfile can crash on long Vorbis writes).
"""
import os

import numpy as np
from gen_entity_sounds import RATE, band, place, seconds
from oggutil import write_ogg

ROOT = os.path.join(os.path.dirname(__file__), "..")
SOUNDS = os.path.join(ROOT, "assets", "backrooms", "sounds")


def write(folder, name, signal, peak, fade=True):
    path = os.path.join(SOUNDS, *folder.split("/"), name + ".ogg")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    signal = np.asarray(signal, dtype=np.float64)
    n = min(len(signal) // 4, int(0.01 * RATE))
    if fade and n > 0:
        signal[:n] *= np.linspace(0, 1, n)
        signal[-n:] *= np.linspace(1, 0, n)
    signal = peak * signal / max(1e-9, np.max(np.abs(signal)))
    if write_ogg(path, signal, RATE):
        print("wrote", os.path.relpath(path, ROOT))


def reverb(signal, decay=0.35, loop=False):
    """A small room: a few early reflections and a soft noise tail, convolved by FFT (fast on long loops).
    With loop=True the tail wraps round, so a loop stays seamless."""
    n = len(signal)
    taps = ((0.031, 0.5), (0.053, 0.35), (0.087, 0.25), (0.131, 0.15))
    k = np.zeros(int(0.6 * RATE))
    k[0] = 1.0
    for delay, gain in taps:
        k[int(delay * RATE)] += gain
    k += 0.02 * np.exp(-np.arange(len(k)) / (decay * RATE)) * band(np.random.default_rng(6).normal(size=len(k)), 150, 3000)
    size = n + len(k) if not loop else n
    if loop:
        kk = np.zeros(n)
        kk[:len(k)] = k
        return np.fft.irfft(np.fft.rfft(signal) * np.fft.rfft(kk), n=n)
    m = 1
    while m < size:
        m *= 2
    return np.fft.irfft(np.fft.rfft(signal, m) * np.fft.rfft(k, m), n=m)[:n]


def wrap(out, n):
    """Folds whatever rings past the end of a loop back onto its start, so the loop is seamless."""
    loop = out[:n].copy()
    tail = out[n:]
    loop[:len(tail)] += tail[:n]
    return loop


NOTE = {"C": -9, "D": -7, "E": -5, "F": -4, "G": -2, "A": 0, "B": 2}


def freq(name):
    """'E4' -> Hz."""
    return 440.0 * 2 ** ((NOTE[name[0]] + 12 * (int(name[1]) - 4)) / 12)


# Brahms, Wiegenlied (Op. 49 No. 4), in C, as a music box plays it: (note, beats)
LULLABY = [("E4", .5), ("E4", .5), ("G4", 2), ("E4", .5), ("E4", .5), ("G4", 2), ("E4", .5), ("G4", .5), ("C5", 1), ("B4", 1.5), ("A4", .5), ("A4", 1), ("G4", 1),
           ("D4", .5), ("E4", .5), ("F4", 1), ("D4", 1), ("D4", .5), ("E4", .5), ("F4", 2), ("D4", .5), ("F4", .5), ("B4", .5), ("A4", .5), ("G4", 1), ("B4", 1), ("C5", 2),
           ("C4", .5), ("C4", .5), ("C5", 2), ("A4", .5), ("F4", .5), ("G4", 2), ("E4", .5), ("C4", .5), ("F4", 1), ("G4", 1), ("A4", 1), ("G4", 2),
           ("C4", .5), ("C4", .5), ("C5", 2), ("A4", .5), ("F4", .5), ("G4", 2), ("E4", .5), ("C4", .5), ("F4", 1), ("E4", 1), ("D4", 1), ("C4", 3)]
BASS = {0: "C3", 3: "C3", 6: "G2", 9: "C3", 13: "G2", 16: "G2", 19: "G2", 22: "C3", 26: "F2", 29: "C3", 32: "G2", 35: "C3", 39: "F2", 42: "C3", 45: "G2", 48: "C3"}


def tine(f, length, rng, detune=0.0, flutter=None):
    """One comb tine: a bright fundamental, an inharmonic upper partial that dies fast, a little click."""
    t = seconds(length)
    f = f * (1 + detune)
    mod = 1.0 if flutter is None else flutter[:len(t)]
    ph = 2 * np.pi * np.cumsum(f * mod) / RATE
    tone = (np.sin(ph) * np.exp(-t * 1.6) + 0.35 * np.sin(5.4 * ph) * np.exp(-t * 9) + 0.18 * np.sin(2 * ph) * np.exp(-t * 4))
    click = band(rng.normal(size=len(t)), 2500, 7000) * np.exp(-t * 400) * 0.08
    return tone * np.minimum(1, t / 0.002) + click


def music_box(total, speed=1.0, detune=0.0, warp=False, seed=974):
    rng = np.random.default_rng(seed)
    beats = sum(d for _, d in LULLABY)
    beat = total / beats
    n = int(total * RATE)
    out = np.zeros(n + int(4 * RATE))
    flutter = None
    if warp:
        tt = np.arange(len(out)) / RATE
        flutter = 1 + 0.012 * np.sin(2 * np.pi * 0.45 * tt) + 0.003 * np.sin(2 * np.pi * 6.2 * tt)
    at = 0.0
    for i, (name, dur) in enumerate(LULLABY):
        if not (warp and rng.random() < 0.07):          # a note now and then missing
            f = 2 * freq(name)                           # a music box sits an octave up
            fl = flutter[int(at * RATE):] if flutter is not None else None
            place(out, tine(f, 3.0, rng, detune, fl), at)
        if i in BASS:
            fl = flutter[int(at * RATE):] if flutter is not None else None
            place(out, 0.45 * tine(2 * freq(BASS[i]), 2.5, rng, detune, fl), at)
        at += dur * beat
    loop = wrap(out, n)
    # Distant and muffled, in a small carpeted room
    loop = band(loop, 180, 2600)
    loop = reverb(loop, decay=0.25, loop=True)
    # A gentle limiter, so one loud tine does not make the rest of the tune whisper
    loop = np.tanh(1.2 * loop / np.percentile(np.abs(loop), 99.7))
    return loop + 0.004 * band(rng.normal(size=n), 200, 3000)


def ambient():
    write("ambient/974", "lullaby", music_box(32.0), 0.45, fade=False)
    write("ambient/974", "lullaby-warped", music_box(36.0, detune=-0.018, warp=True, seed=9741), 0.32, fade=False)

    # The fridge: a 60 Hz compressor hum, its harmonics, a soft rattle that comes and goes (whole cycles: it loops)
    n = int(6 * RATE)
    t = np.arange(n) / RATE
    rng = np.random.default_rng(9742)
    hum = np.sin(2 * np.pi * 60 * t) + 0.5 * np.sin(2 * np.pi * 120 * t) + 0.25 * np.sin(2 * np.pi * 180 * t) + 0.1 * np.sin(2 * np.pi * 240 * t)
    rattle = band(rng.normal(size=n), 400, 1800) * (0.5 + 0.5 * np.sin(2 * np.pi * t / 3)) ** 4 * (np.sin(2 * np.pi * 30 * t) > 0.6)
    write("ambient/974", "fridge", hum * (1 + 0.05 * np.sin(2 * np.pi * t / 2)) + 0.25 * rattle, 0.35, fade=False)

    # The house settling: wood creaks, stick-slip pulses through a few woody resonances
    for k in range(3):
        rng = np.random.default_rng(9750 + k)
        length = 1.0 + 0.4 * k
        n = int(length * RATE)
        out = np.zeros(n)
        tpos, rate = 0.08, rng.uniform(35, 60)
        while tpos < length - 0.15:
            env = np.sin(np.pi * tpos / length)
            pulse = rng.normal(size=int(0.004 * RATE)) * env
            place(out, pulse, tpos)
            tpos += 1 / (rate * (0.8 + 0.6 * env + 0.1 * rng.random()))
        body = np.zeros(n)
        for f0, q in ((rng.uniform(280, 360), 18), (rng.uniform(620, 760), 14), (rng.uniform(1100, 1400), 10)):
            tt = np.arange(int(0.05 * RATE)) / RATE
            kern = np.sin(2 * np.pi * f0 * tt) * np.exp(-tt * f0 / q)
            body += np.convolve(out, kern, mode="same")
        write("ambient/974", f"creak{k + 1}", reverb(band(body, 150, 3000), decay=0.3), 0.4)

    # The computer: an original four-note start-up chime over a warm pad (not anyone's), and a soft mail ding
    n = int(2.5 * RATE)
    out = np.zeros(n)
    rng = np.random.default_rng(9760)
    t = seconds(2.4)
    pad = sum(np.sin(2 * np.pi * f * (1 + d) * t) for f in (freq("C4"), freq("G4"), freq("E5")) for d in (-0.003, 0.003))
    out[:len(t)] += 0.25 * pad * np.minimum(1, t / 0.4) * np.exp(-t * 1.1)
    for i, name in enumerate(("G4", "D5", "B4", "G5")):
        bell = tine(freq(name), 2.0, rng)
        place(out, 0.8 * bell, 0.05 + i * 0.28)
    write("ambient/974", "chime", reverb(band(out, 120, 6000), decay=0.4), 0.5)
    out = np.zeros(int(0.6 * RATE))
    place(out, tine(freq("E5") * 2, 0.6, rng), 0.0)
    place(out, 0.8 * tine(freq("C5") * 2, 0.5, rng), 0.11)
    write("ambient/974", "mail", out, 0.4)

    # Drowsy: a descending celesta glissando into a soft pad
    n = int(3.0 * RATE)
    out = np.zeros(n)
    scale = ["C6", "B5", "A5", "G5", "F5", "E5", "D5", "C5", "B4", "A4", "G4", "E4"]
    for i, name in enumerate(scale):
        f = freq(name[0] + str(int(name[1]))) if len(name) == 2 else freq(name)
        place(out, 0.6 * tine(f, 1.6, rng), i * 0.09)
    t = seconds(2.0)
    pad = sum(np.sin(2 * np.pi * f * t) for f in (freq("C4"), freq("E4"), freq("G4")))
    place(out, 0.3 * pad * np.sin(np.pi * t / 2.0), 0.9)
    write("ambient/974", "drowsy", reverb(band(out, 120, 5000), decay=0.6), 0.45)

    # The lights going out: a relay's clunk and the tick of a cooling filament
    n = int(0.5 * RATE)
    out = np.zeros(n)
    t = seconds(0.12)
    clunk = np.sin(2 * np.pi * 95 * t) * np.exp(-t * 40) + 0.5 * band(rng.normal(size=len(t)), 300, 2500) * np.exp(-t * 80)
    place(out, clunk, 0.01)
    t = seconds(0.02)
    place(out, 0.25 * band(rng.normal(size=len(t)), 3000, 9000) * np.exp(-t * 300), 0.31)
    write("ambient/974", "lightsout", out, 0.6)


def creature():
    # Kitty's rustle: a whisper of heavy cloth, a few soft brushes
    for k in range(3):
        rng = np.random.default_rng(9770 + k)
        n = int(0.6 * RATE)
        out = np.zeros(n)
        for _ in range(rng.integers(2, 4)):
            length = rng.uniform(0.12, 0.25)
            t = seconds(length)
            brush = band(rng.normal(size=len(t)), 900, 6000) * np.sin(np.pi * t / length) ** 2
            place(out, brush * rng.uniform(0.5, 1), rng.uniform(0, 0.6 - length))
        write("creature/974", f"rustle{k + 1}", out, 0.35)
    # A purr: a low breathy hum beating at 25 Hz, in on the breath and out again
    rng = np.random.default_rng(9780)
    n = int(2.5 * RATE)
    t = np.arange(n) / RATE
    rasp = band(rng.normal(size=n), 40, 400)
    tone = np.sin(2 * np.pi * 55 * t) + 0.4 * np.sin(2 * np.pi * 110 * t)
    beat = (0.5 + 0.5 * np.sin(2 * np.pi * 25 * t)) ** 3
    breath = np.sin(np.pi * np.minimum(1, (t % 1.25) / 1.25)) ** 1.5
    write("creature/974", "purr", (0.5 * tone + rasp) * beat * breath, 0.45)
    # A long, low breath out (the offence)
    n = int(2.0 * RATE)
    t = np.arange(n) / RATE
    air = band(rng.normal(size=n), 150, 1400) + 0.4 * band(rng.normal(size=n), 400, 900)
    env = np.minimum(1, t / 0.25) * np.exp(-((t - 0.3) / 1.3) ** 2 * (t > 0.3))
    write("creature/974", "exhale", reverb(air * env, decay=0.4), 0.45)


def generate():
    ambient()
    creature()
