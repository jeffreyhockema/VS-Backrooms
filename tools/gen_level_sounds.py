"""Synthesises the sounds of Levels 37 and 94.

Level 37, the Poolrooms: a drip somewhere off in the tile, water lapping at the edge of a pool, the room tone of a
vast tiled space with no echo where there should be one, and the far-off chanting that draws people into the Sanguine
Reservoir.

Level 94, Motion: the happy little tune the siren poles play all day (a calliope through an old loudspeaker), the same
tune slowed and gone flat for the last hours of the afternoon, distant cartoon laughter at night, a murmured "All
glory to the King!", and the wind-up whirr of a Robo-Man.

Run from the repo root:  python tools/gen_level_sounds.py
"""
import os

import numpy as np
from oggutil import write_ogg

from gen_entity_sounds import RATE, band, place, reverb, seconds, vowel

ROOT = os.path.join(os.path.dirname(__file__), "..")
SOUNDS = os.path.join(ROOT, "assets", "backrooms", "sounds")


def write(folder, name, signal, peak, fade=True):
    """Normalises and writes an OGG a little at a time (libsndfile can crash on long Vorbis buffers)."""
    path = os.path.join(SOUNDS, folder, name + ".ogg")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    signal = np.asarray(signal, dtype=np.float64)
    n = min(len(signal) // 4, int(0.01 * RATE))
    if fade and n > 0:
        signal[:n] *= np.linspace(0, 1, n)
        signal[-n:] *= np.linspace(1, 0, n)
    signal = peak * signal / max(1e-9, np.max(np.abs(signal)))
    if write_ogg(path, signal, RATE):
        print("wrote", os.path.relpath(path, ROOT))


# ======================= Level 37 =======================

def tile_room(signal, wet=0.25):
    """A tiled room that should ring and doesn't: a few hard early reflections, then the sound simply stops."""
    out = np.copy(signal)
    for delay, gain in ((0.011, 0.35), (0.019, 0.25), (0.027, 0.18)):
        d = int(delay * RATE)
        out[d:] += gain * wet * 4 * signal[:-d]
    return out


def pooldrip():
    rng = np.random.default_rng(3701)
    t = seconds(0.9)
    # A drop: a rising plink, then a softer second one
    f = 900 * (1 + 2.5 * np.minimum(t, 0.03) / 0.03)
    drop = np.sin(2 * np.pi * np.cumsum(f) / RATE) * np.exp(-t * 45)
    out = np.zeros(len(t))
    place(out, drop, 0.02)
    place(out, 0.35 * drop[: int(0.2 * RATE)], 0.24)
    out += 0.02 * band(rng.normal(size=len(t)), 2000, 7000) * np.exp(-t * 60)
    write("ambient", "pooldrip", tile_room(out), 0.6)


def poollap():
    rng = np.random.default_rng(3702)
    n = int(3.0 * RATE)
    out = np.zeros(n)
    for k in range(5):
        t = seconds(rng.uniform(0.3, 0.6))
        slap = band(rng.normal(size=len(t)), 150, 1800) * np.sin(np.pi * t / t[-1]) ** 2
        place(out, slap * rng.uniform(0.4, 1), rng.uniform(0, 2.4))
    write("ambient", "poollap", tile_room(out, 0.15), 0.5)


def poolroom():
    """The Poolrooms' room tone, a seamless loop: a very soft wash of water, the odd lap at an edge."""
    rng = np.random.default_rng(3703)
    n = int(12.0 * RATE)
    spectrum = rng.normal(size=n // 2 + 1) + 1j * rng.normal(size=n // 2 + 1)
    f = np.fft.rfftfreq(n, 1 / RATE)
    spectrum *= np.exp(-((f - 400) / 500) ** 2) + 0.2 * np.exp(-((f - 1500) / 800) ** 2)
    wash = np.fft.irfft(spectrum, n=n)
    t = np.arange(n) / RATE
    # Swells in whole cycles, so the loop is seamless
    wash *= 0.6 + 0.4 * np.sin(2 * np.pi * t / 6) ** 2
    write("ambient", "poolroom", wash, 0.12, fade=False)


def chant():
    """Many voices far away, chanting the same few syllables over and over: the Reservoir calling."""
    rng = np.random.default_rng(3704)
    n = int(9.0 * RATE)
    out = np.zeros(n)
    vowels = [((700, 130, 1), (1100, 150, 0.6)), ((400, 100, 1), (800, 120, 0.7)), ((300, 90, 1), (2200, 250, 0.4))]
    pattern = [0, 1, 1, 2, 0, 1]
    for voice in range(9):
        base = rng.uniform(95, 180)
        at = rng.uniform(0, 0.08)
        for rep in range(3):
            for k, v in enumerate(pattern):
                length = 0.42 if k % 3 == 2 else 0.3
                t = seconds(length)
                f0 = base * (1 + 0.03 * np.sin(2 * np.pi * 5 * t))
                syl = vowel(t, f0, vowels[v], 0.08, rng) * np.sin(np.pi * t / length) ** 1.2
                place(out, syl * rng.uniform(0.5, 1), at)
                at += length + 0.05
            at += 0.5
    write("ambient", "chant", reverb(band(out, 100, 1200), decay=0.6), 0.35)


# ======================= Level 94 =======================

NOTES = {"C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.00, "A4": 440.00, "B4": 493.88,
         "C5": 523.25, "D5": 587.33, "E5": 659.25, "F5": 698.46, "G5": 783.99, "A5": 880.00}

# A bouncy little tune in C, the kind a cartoon of the 1930s opens with: melody, then an oom-pah bass
MELODY = [("E5", 1), ("G5", 1), ("C5", 1), ("E5", 1), ("D5", 1), ("F5", 1), ("A4", 2),
          ("G4", 1), ("B4", 1), ("D5", 1), ("G5", 1), ("F5", 1), ("E5", 1), ("C5", 2),
          ("E5", 1), ("G5", 1), ("A5", 1), ("G5", 1), ("F5", 1), ("D5", 1), ("B4", 2),
          ("C5", 1), ("E5", 1), ("D5", 1), ("B4", 1), ("C5", 3), (None, 1)]
BASS = ["C4", "G4", "C4", "G4", "F4", "C4", "F4", "C4", "G4", "D4", "G4", "D4", "C4", "G4", "C4", "G4",
        "C4", "G4", "F4", "C4", "G4", "D4", "G4", "B4", "C4", "G4", "C4", "C4"]


def calliope(freq, length, detune=0.0):
    """One note of a steam calliope through an old horn speaker: a breathy pipe with a wobble."""
    t = seconds(length)
    f = freq * (1 + detune) * (1 + 0.006 * np.sin(2 * np.pi * 6 * t))
    phase = 2 * np.pi * np.cumsum(f) / RATE
    tone = np.sin(phase) + 0.45 * np.sin(2 * phase) + 0.25 * np.sin(3 * phase) + 0.12 * np.sin(5 * phase)
    env = np.minimum(1, t / 0.02) * np.exp(-t * 1.2)
    return tone * env


def tune(beat, detune_drift=0.0):
    """The siren poles' tune, beat seconds to a beat; detune_drift bends it flatter as it goes."""
    beats = sum(d for _, d in MELODY)
    n = int(beats * beat * RATE)
    out = np.zeros(n)
    at = 0.0
    for name, dur in MELODY:
        if name:
            drift = -detune_drift * at / (beats * beat)
            place(out, calliope(NOTES[name], dur * beat * 0.95, drift), at)
        at += dur * beat
    for k, name in enumerate(BASS):
        if k * beat >= beats * beat:
            break
        drift = -detune_drift * k / len(BASS)
        place(out, 0.5 * calliope(NOTES[name] / 2, beat * 0.4, drift), k * beat)
    # A little glockenspiel on the strong beats
    for k in range(0, int(beats), 4):
        t = seconds(0.4)
        place(out, 0.25 * np.sin(2 * np.pi * NOTES["C5"] * 2 * t) * np.exp(-t * 9), k * beat)
    # Through an old loudspeaker on a pole: the lows and highs gone, a little crackle
    rng = np.random.default_rng(9401)
    out = band(out, 280, 3800)
    out += 0.015 * band(rng.normal(size=n), 1000, 6000) * (rng.random(n) < 0.02)
    return np.tanh(1.3 * out / np.max(np.abs(out)))


def sirentune():
    write("ambient", "sirentune", tune(0.28), 0.5)
    # The last hours of the afternoon: slower, and sliding flat as it goes
    write("ambient", "sirentune-dusk", tune(0.36, detune_drift=0.06), 0.45)


def laughter():
    """Cartoon laughter from somewhere off over the hills: a high 'ha-ha-ha' that bounces, and echoes."""
    rng = np.random.default_rng(9402)
    n = int(2.6 * RATE)
    out = np.zeros(n)
    for voice, base in enumerate((310, 250)):
        at = 0.05 + voice * 0.35
        for k in range(rng.integers(5, 8)):
            length = 0.13
            t = seconds(length)
            f0 = base * (1.15 - 0.04 * k) * (1 + 0.15 * (1 - t / length))
            syl = vowel(t, f0, ((800, 150, 1), (1300, 180, 0.6)), 0.3, rng) * np.sin(np.pi * t / length)
            place(out, syl * (1 - 0.08 * k), at)
            at += 0.17 + rng.uniform(0, 0.03)
    write("entity", "laughter", reverb(band(out, 200, 3200), decay=0.5), 0.55)


def allglory():
    """A crowd of small voices, close together, murmuring 'All glory to the King!'"""
    rng = np.random.default_rng(9403)
    # all - glo - ry - to - the - King
    syllables = [((700, 120, 1), (1150, 140, 0.6), 0.22), ((450, 100, 1), (850, 120, 0.7), 0.2), ((350, 90, 1), (2100, 200, 0.5), 0.18),
                 ((300, 80, 1), (900, 120, 0.5), 0.14), ((450, 100, 1), (1600, 180, 0.4), 0.12), ((350, 90, 1), (2300, 220, 0.5), 0.42)]
    n = int(2.4 * RATE)
    out = np.zeros(n)
    for voice in range(7):
        base = rng.uniform(170, 290)
        at = 0.05 + rng.uniform(0, 0.06)
        for k, (f1, f2, length) in enumerate(syllables):
            t = seconds(length)
            rise = 1.12 if k == len(syllables) - 1 else 1.0
            f0 = base * rise * (1 + 0.02 * np.sin(2 * np.pi * 7 * t))
            syl = vowel(t, f0, (f1, f2), 0.12, rng) * np.sin(np.pi * t / length) ** 1.2
            place(out, syl * rng.uniform(0.5, 1), at)
            at += length + 0.03
    write("entity", "allglory", reverb(band(out, 150, 2600), decay=0.4), 0.5)


def robowind():
    """A clockwork key being wound, ratchet click by click, then the whirr of a tin mechanism starting up."""
    rng = np.random.default_rng(9404)
    n = int(1.8 * RATE)
    out = np.zeros(n)
    for k in range(9):
        t = seconds(0.03)
        click = band(rng.normal(size=len(t)), 2000, 8000) * np.exp(-t * 300)
        place(out, click * (0.7 + 0.3 * (k % 2)), 0.05 + k * 0.08)
    t = seconds(0.9)
    whirr = np.sin(2 * np.pi * np.cumsum(180 + 220 * np.minimum(1, t / 0.4)) / RATE)
    whirr = np.sign(whirr) * np.abs(whirr) ** 0.5 * np.minimum(1, t / 0.05) * np.exp(-t * 2)
    place(out, 0.4 * band(whirr, 200, 5000), 0.82)
    write("entity", "robowind", out, 0.55)


def main():
    pooldrip()
    poollap()
    poolroom()
    chant()
    sirentune()
    laughter()
    allglory()
    robowind()


if __name__ == "__main__":
    main()
