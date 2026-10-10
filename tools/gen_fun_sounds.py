"""Synthesises Level Fun =)'s sounds (docs/new-levels/fun-plan.md, 4.5): mono OGG, written in chunks.

- ambient/fun/: the distant party (an original waltz on a music box and toy organ through two walls), the speakers'
  "Happy Birthday to You" (the melody is public domain) on a tinny toy organ with tape warble, the tape catching, the
  bounce-house blower, the deck's wind and hull-slap, a cheer, a party horn, a balloon pop, a party popper, a far
  wordless chorus of "happy birthday", the Host's breathing, sob and wail, and the Carnivorous Balloons' sting and gas.
- entity/partygoer/: soft rubbery steps, the gaze's thin whine, the latch, the carapace, the claws, the death hiss.

Loops are rendered on a circle (tails folded back onto the start) so they repeat without a seam.
Run through gen_fun.py, or alone:   bash tools/locked.sh run python tools/gen_fun_sounds.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from gen_entity_sounds import RATE, band, place, reverb, seconds, vowel  # noqa: E402
from gen_level_sounds import write  # noqa: E402

AMB, ENT = os.path.join("ambient", "fun"), os.path.join("entity", "partygoer")


def note(name):
    """Frequency of a note name like 'C5', 'F#4', 'Bb4'."""
    names = {"C": -9, "D": -7, "E": -5, "F": -4, "G": -2, "A": 0, "B": 2}
    n = names[name[0]]
    rest = name[1:]
    if rest[0] in "#b":
        n += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    return 440.0 * 2 ** ((n + 12 * (int(rest) - 4)) / 12)


def loop_place(out, sound, at):
    """Adds a sound into a loop buffer, wrapping what runs past the end round to the start."""
    i = int(at * RATE) % len(out)
    n = len(sound)
    first = min(n, len(out) - i)
    out[i:i + first] += sound[:first]
    if n > first:
        rest = sound[first:]
        while len(rest):
            m = min(len(rest), len(out))
            out[:m] += rest[:m]
            rest = rest[m:]


# ======================= Instruments

def music_box(freq, length=1.6):
    """A music-box tine: a bright sine and an inharmonic overtone, dying away."""
    t = seconds(length)
    return (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 4.2 * t) * np.exp(-t * 9)) * np.exp(-t * 3.2) * np.minimum(1, t / 0.003)


def toy_organ(freq, length, warble=None):
    """A cheap toy organ: a soft square-ish reed with a little vibrato; `warble` (an array of cents) bends it."""
    t = seconds(length)
    f = freq * (1 + 0.004 * np.sin(2 * np.pi * 5.5 * t))
    if warble is not None:
        f = f * 2 ** (warble[: len(t)] / 1200)
    ph = 2 * np.pi * np.cumsum(f) / RATE
    tone = np.sin(ph) + 0.33 * np.sin(3 * ph) + 0.2 * np.sin(5 * ph) + 0.12 * np.sin(7 * ph) + 0.25 * np.sin(2 * ph)
    env = np.minimum(1, t / 0.015) * np.minimum(1, (length - t) / 0.04) * (0.85 + 0.15 * np.exp(-t * 4))
    return tone * env


def lowpass(x, fc, order=2):
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / RATE)
    spec /= (1 + (f / fc) ** (2 * order)) ** 0.5
    return np.fft.irfft(spec, n=len(x))


# ======================= The distant party: an original waltz, heard through two walls

# (bar by bar, 3/4; (note, beats))
WALTZ = [
    [("E5", 1), ("G5", 1), ("C6", 1)], [("B5", 2), ("G5", 1)], [("A5", 1), ("F5", 1), ("D5", 1)], [("G5", 3)],
    [("F5", 1), ("A5", 1), ("D6", 1)], [("C6", 2), ("A5", 1)], [("G5", 1), ("E5", 1), ("C5", 1)], [("D5", 3)],
    [("E5", 1), ("G5", 1), ("C6", 1)], [("D6", 2), ("B5", 1)], [("C6", 1), ("A5", 1), ("F5", 1)], [("E5", 2), ("G5", 1)],
    [("F5", 1), ("D5", 1), ("B4", 1)], [("C5", 1), ("E5", 1), ("G5", 1)], [("D5", 2), ("B4", 1)], [("C5", 3)],
]
CHORDS = [("C3", ["E4", "G4", "C5"]), ("G2", ["D4", "G4", "B4"]), ("F2", ["F4", "A4", "D5"]), ("G2", ["D4", "G4", "B4"]),
          ("F2", ["F4", "A4", "C5"]), ("F2", ["F4", "A4", "C5"]), ("C3", ["E4", "G4", "C5"]), ("G2", ["D4", "F4", "B4"]),
          ("C3", ["E4", "G4", "C5"]), ("G2", ["D4", "G4", "B4"]), ("F2", ["F4", "A4", "C5"]), ("C3", ["E4", "G4", "C5"]),
          ("G2", ["D4", "F4", "B4"]), ("C3", ["E4", "G4", "C5"]), ("G2", ["D4", "F4", "B4"]), ("C3", ["E4", "G4", "C5"])]


def partydistant():
    length, beat = 24.0, 0.5
    detune = 2 ** (-15 / 1200)
    out = np.zeros(int(length * RATE))
    at = 0.0
    for bar, chord in zip(WALTZ, CHORDS):
        b0 = at
        for name, beats in bar:
            loop_place(out, music_box(note(name) * detune, 1.8), at)
            at += beats * beat
        bass, triad = chord
        loop_place(out, 0.5 * toy_organ(note(bass) * detune, beat * 0.9), b0)
        for k in (1, 2):
            for nm in triad:
                loop_place(out, 0.16 * toy_organ(note(nm) * detune, beat * 0.6), b0 + k * beat)
    music = lowpass(out, 600, 2)
    # A crowd murmuring under it, far off: vowels with no words in them
    rng = np.random.default_rng(1501)
    crowd = np.zeros(len(out))
    for voice in range(10):
        base = rng.uniform(100, 230)
        tt = rng.uniform(0, length)
        while tt < length + 2:
            ln = rng.uniform(0.12, 0.3)
            t = seconds(ln)
            v = rng.choice(4)
            form = [((700, 120, 1), (1200, 150, 0.6)), ((400, 100, 1), (2000, 200, 0.5)), ((500, 100, 1), (900, 120, 0.6)), ((300, 80, 1), (2300, 250, 0.4))][v]
            syl = vowel(t, base * (1 + 0.04 * np.sin(2 * np.pi * 3 * t)), form, 0.1, rng) * np.sin(np.pi * t / ln)
            loop_place(crowd, syl * rng.uniform(0.3, 1), tt)
            tt += ln + rng.uniform(0.02, 0.5)
    crowd = lowpass(crowd, 500, 2)
    mix = music / np.max(np.abs(music)) + 0.22 * crowd / np.max(np.abs(crowd))
    write(AMB, "partydistant", mix, 0.10, fade=False)


# ======================= Happy Birthday to You (public domain melody), on the speakers

BIRTHDAY = [("G4", 0.75), ("G4", 0.25), ("A4", 1), ("G4", 1), ("C5", 1), ("B4", 2),
            ("G4", 0.75), ("G4", 0.25), ("A4", 1), ("G4", 1), ("D5", 1), ("C5", 2),
            ("G4", 0.75), ("G4", 0.25), ("G5", 1), ("E5", 1), ("C5", 1), ("B4", 1), ("A4", 2),
            ("F5", 0.75), ("F5", 0.25), ("E5", 1), ("C5", 1), ("D5", 1), ("C5", 3)]
BIRTHDAY_CHORDS = [(0, "C3"), (3, "G2"), (6, "G2"), (9, "C3"), (12, "C3"), (15, "F2"), (18, "F2"), (21, "C3"), (22.5, "G2"), (24, "C3")]


def funtune():
    length = 20.0
    beat = length / 30  # 26 beats of tune and a breath before it comes round again
    n = int(length * RATE)
    tt = np.arange(n) / RATE
    warble = 8 * np.sin(2 * np.pi * 0.7 * tt)  # tape warble, cents
    out = np.zeros(n)
    at = beat
    for name, beats in BIRTHDAY:
        i = int(at * RATE)
        loop_place(out, toy_organ(note(name), beats * beat * 0.92, np.roll(warble, -i)), at)
        at += beats * beat
    for b, bass in BIRTHDAY_CHORDS:
        start = beat + b * beat
        loop_place(out, 0.35 * toy_organ(note(bass) * 2, beat * 0.5, np.roll(warble, -int(start * RATE))), start)
    # Through a small wall speaker: no lows, no highs, a little hiss
    rng = np.random.default_rng(1502)
    out = band(out, 400, 3500)
    out = np.tanh(1.6 * out / np.max(np.abs(out)))
    out += 0.02 * band(rng.normal(size=n), 2000, 7000)
    write(AMB, "funtune", out, 0.25, fade=False)


def funtune_skip():
    """The tape catching: the tune slurs down and stops with a clunk."""
    rng = np.random.default_rng(1503)
    t = seconds(1.5)
    f = note("C5") * np.maximum(0.15, 1 - 0.75 * t / 1.0) * (1 + 0.04 * np.sin(2 * np.pi * 11 * t))
    ph = 2 * np.pi * np.cumsum(f) / RATE
    tone = (np.sin(ph) + 0.3 * np.sin(3 * ph)) * np.maximum(0, 1 - t / 1.05)
    out = band(tone, 300, 3500)
    clunk = band(rng.normal(size=int(0.08 * RATE)), 80, 1500) * np.exp(-seconds(0.08) * 60)
    place(out, 1.5 * clunk, 1.05)
    write(AMB, "funtune-skip", out, 0.3)


# ======================= Machines, wind and water

def blower():
    rng = np.random.default_rng(1504)
    n = int(6.0 * RATE)
    t = np.arange(n) / RATE
    rush = band(rng.normal(size=n), 120, 2500)
    rush = np.fft.irfft(np.fft.rfft(rush) * (1 / (1 + np.fft.rfftfreq(n, 1 / RATE) / 800)), n=n)
    motor = np.sin(2 * np.pi * 140 * t) + 0.4 * np.sin(2 * np.pi * 280 * t) + 0.15 * np.sin(2 * np.pi * 420 * t)
    out = rush / np.max(np.abs(rush)) + 0.25 * motor
    write(AMB, "blower", out, 0.3, fade=False)


def deckwind():
    rng = np.random.default_rng(1505)
    n = int(12.0 * RATE)
    t = np.arange(n) / RATE
    wind = lowpass(rng.normal(size=n), 400, 2)
    gust = 0.55 + 0.45 * np.sin(2 * np.pi * t / 6) ** 2 * (0.7 + 0.3 * np.sin(2 * np.pi * t / 4 + 1))
    out = wind / np.max(np.abs(wind)) * gust
    # Water slapping a steel hull far below, now and then
    for k in range(6):
        at = rng.uniform(0, 12)
        ln = rng.uniform(0.3, 0.6)
        tt = seconds(ln)
        slap = band(rng.normal(size=len(tt)), 100, 900) * np.sin(np.pi * tt / ln) ** 3
        loop_place(out, 0.6 * slap / np.max(np.abs(slap)), at)
    write(AMB, "deckwind", out, 0.35, fade=False)


# ======================= Far-off party noises

def cheer():
    rng = np.random.default_rng(1506)
    n = int(3.0 * RATE)
    out = np.zeros(n)
    for voice in range(14):
        base = rng.uniform(160, 380)
        ln = rng.uniform(0.8, 1.6)
        t = seconds(ln)
        f0 = base * (1 + 0.25 * np.exp(-t * 3)) * (1 + 0.02 * np.sin(2 * np.pi * 6 * t))
        v = vowel(t, f0, ((750, 160, 1), (1250, 180, 0.6)), 0.25, rng) * np.sin(np.pi * t / ln) ** 0.6
        place(out, v * rng.uniform(0.4, 1), rng.uniform(0, 0.4))
    # A clatter of clapping
    for k in range(60):
        c = band(rng.normal(size=int(0.02 * RATE)), 800, 5000) * np.exp(-seconds(0.02) * 200)
        place(out, 0.4 * c, rng.uniform(0.1, 2.4))
    write(AMB, "cheer", reverb(lowpass(out, 2500), decay=0.6), 0.45)


def partyhorn():
    """A blowout horn: a buzzy reed, rising a little as the paper unrolls, then the wheeze as it curls back."""
    rng = np.random.default_rng(1507)
    t = seconds(1.2)
    f = 420 * (1 + 0.08 * np.minimum(1, t / 0.15)) * (1 + 0.01 * rng.normal(size=len(t)).cumsum() / 400)
    ph = 2 * np.pi * np.cumsum(f) / RATE
    buzz = np.sign(np.sin(ph)) * 0.6 + np.sin(2 * ph) * 0.3
    env = np.minimum(1, t / 0.03) * np.where(t < 0.8, 1.0, np.maximum(0, 1 - (t - 0.8) / 0.35))
    out = band(buzz * env, 300, 4000) + 0.15 * band(rng.normal(size=len(t)), 1500, 6000) * env
    write(AMB, "partyhorn", reverb(out, decay=0.5), 0.35)


def balloonpop():
    rng = np.random.default_rng(1508)
    n = int(0.4 * RATE)
    t = np.arange(n) / RATE
    crack = rng.normal(size=n) * np.exp(-t * 90)
    thump = np.sin(2 * np.pi * 90 * t) * np.exp(-t * 40)
    out = band(crack, 200, 9000) + 0.6 * thump
    for d, g in ((0.013, 0.4), (0.021, 0.3), (0.034, 0.2)):  # a small room's first reflections
        k = int(d * RATE)
        out[k:] += g * out[:-k]
    write(AMB, "balloonpop", out, 0.8)


def popper():
    rng = np.random.default_rng(1509)
    n = int(1.5 * RATE)
    out = np.zeros(n)
    t = seconds(0.15)
    place(out, band(rng.normal(size=len(t)), 300, 8000) * np.exp(-t * 60) + 0.5 * np.sin(2 * np.pi * 120 * t) * np.exp(-t * 30), 0.02)
    # Confetti settling: a fine paper rustle
    t = seconds(1.2)
    rustle = band(rng.normal(size=len(t)), 3000, 9000) * (rng.random(len(t)) < 0.08) * np.exp(-t * 2.5)
    place(out, 0.35 * rustle, 0.2)
    write(AMB, "popper", out, 0.8)


def singing():
    """Many voices far away singing "happy birthday" with no words, slow and a little out of time."""
    rng = np.random.default_rng(1510)
    beat = 9.0 / 27
    n = int(9.5 * RATE)
    out = np.zeros(n)
    forms = [((700, 130, 1), (1100, 150, 0.6)), ((450, 100, 1), (900, 120, 0.7)), ((350, 90, 1), (2100, 220, 0.5))]
    for voice in range(12):
        octave = 0.5 if voice % 3 == 0 else 1.0
        at = rng.uniform(0, 0.06)
        drift = rng.uniform(-0.02, 0.02)
        for k, (name, beats) in enumerate(BIRTHDAY):
            ln = beats * beat * 0.95
            t = seconds(ln)
            f0 = note(name) * octave * (1 + drift) * (1 + 0.015 * np.sin(2 * np.pi * 5 * t))
            syl = vowel(t, f0, forms[k % 3], 0.08, rng) * np.sin(np.pi * t / ln) ** 0.8
            place(out, syl * rng.uniform(0.4, 1), at)
            at += beats * beat * rng.uniform(0.98, 1.03)
    write(AMB, "singing", reverb(lowpass(out, 1400), decay=0.9), 0.3)


# ======================= The Host

def hostbreath():
    rng = np.random.default_rng(1511)
    n = int(8.0 * RATE)
    t = np.arange(n) / RATE
    air = lowpass(rng.normal(size=n), 350, 2)
    cycle_ = np.sin(np.pi * t / 4.0) ** 2  # two breaths in eight seconds, in and out
    wet = band(rng.normal(size=n), 200, 1200) * (rng.random(n) < 0.004)
    out = air / np.max(np.abs(air)) * cycle_ + 0.3 * lowpass(wet, 900) / max(1e-9, np.max(np.abs(wet)))
    out += 0.25 * np.sin(2 * np.pi * 38 * t) * cycle_
    write(AMB, "hostbreath", out, 0.4, fade=False)


def hostweep():
    rng = np.random.default_rng(1512)
    n = int(3.0 * RATE)
    out = np.zeros(n)
    for k, at in enumerate((0.1, 0.9, 1.6)):
        ln = 0.6
        t = seconds(ln)
        f0 = 120 * (1.2 - 0.3 * t / ln)
        place(out, vowel(t, f0, ((400, 100, 1), (800, 120, 0.5)), 0.4, rng) * np.sin(np.pi * t / ln), at)
    for k in range(5):  # drips
        t = seconds(0.15)
        f = 700 * (1 + 2 * np.minimum(t, 0.02) / 0.02)
        place(out, 0.4 * np.sin(2 * np.pi * np.cumsum(f) / RATE) * np.exp(-t * 50), rng.uniform(0.3, 2.8))
    write(AMB, "hostweep", reverb(out, decay=0.7), 0.45)


def hostupset():
    rng = np.random.default_rng(1513)
    t = seconds(4.0)
    f0 = 70 * (1 + 0.4 * np.sin(np.pi * t / 4.0)) * (1 + 0.03 * np.sin(2 * np.pi * 4 * t))
    wail = vowel(t, f0, ((500, 140, 1), (850, 160, 0.7), (2400, 300, 0.2)), 0.3, rng) * np.sin(np.pi * t / 4.0) ** 0.7
    write(AMB, "hostupset", reverb(wail, decay=0.9), 0.55)


# ======================= Carnivorous Balloons

def cballoon_sting():
    rng = np.random.default_rng(1514)
    t = seconds(0.6)
    squeak = np.sin(2 * np.pi * np.cumsum(900 + 600 * np.sin(np.pi * t / 0.25)) / RATE) * np.exp(-t * 8) * (t < 0.3)
    whip = band(rng.normal(size=len(t)), 2000, 8000) * np.exp(-((t - 0.32) / 0.02) ** 2)
    write(AMB, "cballoon-sting", squeak + 0.8 * whip, 0.55)


def cballoon_gas():
    rng = np.random.default_rng(1515)
    n = int(2.0 * RATE)
    t = np.arange(n) / RATE
    hiss = band(rng.normal(size=n), 2500, 9000) * np.exp(-t * 1.2)
    out = hiss
    for at in (1.1, 1.45):  # a cough
        tt = seconds(0.18)
        c = vowel(tt, 160 * np.ones(len(tt)), ((600, 200, 1), (1500, 300, 0.5)), 1.5, rng) * np.exp(-tt * 18)
        place(out, 0.9 * c / max(1e-9, np.max(np.abs(c))), at)
    write(AMB, "cballoon-gas", out, 0.5)


# ======================= Partygoers

def steps():
    """A soft rubbery creak underfoot, very quiet."""
    for i in range(3):
        rng = np.random.default_rng(1520 + i)
        t = seconds(0.35)
        f = rng.uniform(180, 260) * (1 + 0.3 * np.sin(2 * np.pi * rng.uniform(15, 30) * t))
        creak = np.sin(2 * np.pi * np.cumsum(f) / RATE) * np.exp(-t * 10) * np.minimum(1, t / 0.02)
        squish = lowpass(rng.normal(size=len(t)), 600) * np.exp(-t * 25)
        write(ENT, f"step{i + 1}", band(creak + 0.8 * squish, 80, 2000), 0.18)


def gaze():
    """The thin high whine of one of them noticing you."""
    t = seconds(1.5)
    f = 3800 + 300 * np.sin(2 * np.pi * 0.7 * t)
    tone = np.sin(2 * np.pi * np.cumsum(f) / RATE) + 0.3 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / RATE)
    env = np.minimum(1, t / 0.5) * np.minimum(1, (1.5 - t) / 0.2)
    write(ENT, "gaze", tone * env, 0.3)


def latch():
    rng = np.random.default_rng(1530)
    n = int(0.8 * RATE)
    t = np.arange(n) / RATE
    suck = lowpass(rng.normal(size=n), 900) * np.exp(-((t - 0.12) / 0.08) ** 2)
    pop_ = np.sin(2 * np.pi * 160 * t) * np.exp(-((t - 0.18) / 0.03) ** 2)
    crunch = band(rng.normal(size=n), 800, 5000) * (rng.random(n) < 0.06) * np.exp(-((t - 0.3) / 0.12) ** 2)
    write(ENT, "latch", suck + 0.6 * pop_ + 0.9 * crunch, 0.7)


def carapace():
    rng = np.random.default_rng(1531)
    n = int(1.0 * RATE)
    t = np.arange(n) / RATE
    crack = band(rng.normal(size=n), 300, 6000) * np.exp(-t * 40) + 0.7 * np.sin(2 * np.pi * 70 * t) * np.exp(-t * 18)
    hiss = band(rng.normal(size=n), 2000, 8000) * np.minimum(1, t / 0.1) * np.exp(-t * 2.5) * 0.35
    write(ENT, "carapace", crack + hiss, 0.75)


def claw():
    rng = np.random.default_rng(1532)
    n = int(0.6 * RATE)
    out = np.zeros(n)
    for k in range(9):  # skittering legs
        c = band(rng.normal(size=int(0.012 * RATE)), 2000, 7000) * np.exp(-seconds(0.012) * 300)
        place(out, 0.5 * c, 0.01 + k * 0.025 + rng.uniform(0, 0.01))
    t = seconds(0.2)
    slash = band(rng.normal(size=len(t)), 1500, 8000) * np.sin(np.pi * t / 0.2) ** 2
    place(out, slash, 0.25)
    write(ENT, "claw", out, 0.6)


def die():
    rng = np.random.default_rng(1533)
    n = int(2.0 * RATE)
    t = np.arange(n) / RATE
    hiss = band(rng.normal(size=n), 1500, 9000) * np.exp(-t * 1.2)
    sizzle = band(rng.normal(size=n), 3000, 9000) * (rng.random(n) < 0.03) * 2
    groan = np.sin(2 * np.pi * np.cumsum(90 * (1 - 0.4 * t / 2)) / RATE) * np.exp(-t * 2) * 0.5
    write(ENT, "die", hiss + sizzle + groan, 0.55)


def main():
    partydistant()
    funtune()
    funtune_skip()
    blower()
    deckwind()
    cheer()
    partyhorn()
    balloonpop()
    popper()
    singing()
    hostbreath()
    hostweep()
    hostupset()
    cballoon_sting()
    cballoon_gas()
    steps()
    gaze()
    latch()
    carapace()
    claw()
    die()


if __name__ == "__main__":
    main()
