"""Synthesises the sounds of the things that live in the Backrooms, and the noises heard down the hall when nothing is
there: footsteps that stop when you stop, scratching inside the walls, a murmur of voices, a cough, a knock, a door
slamming, a phone that rings once, wings, a Smiler's ringing sting, a Duller's grab, a mimic's "hello?".

Every sound is one-shot and dry; the game places it in the world. Run from the repo root:
    python tools/gen_entity_sounds.py
"""
import os

import numpy as np
from oggutil import write_ogg

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "assets", "backrooms", "sounds", "entity")
RATE = 44100


def write(name, signal, peak):
    """Normalises and writes an OGG, a little at a time (libsndfile can crash on long Vorbis buffers)."""
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + ".ogg")
    signal = np.asarray(signal, dtype=np.float64)
    # Short fades so nothing clicks
    fade = min(len(signal) // 4, int(0.01 * RATE))
    if fade > 0:
        signal[:fade] *= np.linspace(0, 1, fade)
        signal[-fade:] *= np.linspace(1, 0, fade)
    signal = peak * signal / max(1e-9, np.max(np.abs(signal)))
    if write_ogg(path, signal, RATE):
        print("wrote", os.path.relpath(path, ROOT))


def band(signal, lo, hi):
    spectrum = np.fft.rfft(signal)
    f = np.fft.rfftfreq(len(signal), 1 / RATE)
    spectrum *= (f >= lo) & (f <= hi)
    return np.fft.irfft(spectrum, n=len(signal))


def seconds(s):
    return np.arange(int(s * RATE)) / RATE


def thud(length, f0, rng, bright=0.3):
    """One impact: a low knock with a little noise on top."""
    t = seconds(length)
    body = np.sin(2 * np.pi * f0 * t * (1 - 0.3 * t / length)) * np.exp(-t * 28)
    click = band(rng.normal(size=len(t)), 300, 3000) * np.exp(-t * 90) * bright
    return body + click


def place(out, sound, at):
    i = int(at * RATE)
    n = min(len(sound), len(out) - i)
    if n > 0:
        out[i:i + n] += sound[:n]


def reverb(signal, decay=0.35, taps=((0.031, 0.5), (0.053, 0.35), (0.087, 0.25), (0.131, 0.15))):
    """A cheap hallway: a few early reflections and a soft tail, so things sound far off down a corridor."""
    out = np.copy(signal)
    for delay, gain in taps:
        d = int(delay * RATE)
        out[d:] += gain * signal[:-d]
    tail = band(np.random.default_rng(5).normal(size=len(signal)), 100, 2500) * 0.002
    kernel = np.exp(-np.arange(int(0.6 * RATE)) / (decay * RATE)) * band(np.random.default_rng(6).normal(size=int(0.6 * RATE)), 150, 3000)
    wet = np.convolve(signal, kernel[: len(kernel)] * 0.02, mode="full")[: len(signal)]
    return out + wet + tail


def footsteps():
    """Heavy, slow steps on a hard floor, five of them, the last a half-step late: then nothing."""
    rng = np.random.default_rng(201)
    out = np.zeros(int(3.6 * RATE))
    for i, at in enumerate((0.1, 0.72, 1.33, 1.95, 2.71)):
        place(out, thud(0.25, rng.uniform(70, 95), rng, 0.6) * (0.75 + 0.25 * (i % 2)), at)
    write("footsteps", reverb(out), 0.7)


def scratch():
    """Something dragging its nails along the inside of the wall."""
    rng = np.random.default_rng(202)
    out = np.zeros(int(2.4 * RATE))
    t0 = 0.05
    while t0 < 2.1:
        n = int(rng.uniform(0.25, 0.6) * RATE)
        t = np.arange(n) / RATE
        stroke = band(rng.normal(size=n), 1500, 6500) * (0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(25, 45) * t) ** 2)
        stroke *= np.sin(np.pi * t / t[-1]) ** 0.5
        place(out, stroke * rng.uniform(0.5, 1.0), t0)
        t0 += rng.uniform(0.35, 0.7)
    # Muffled by plaster
    write("scratch", reverb(band(out, 600, 4500)), 0.55)


def vowel(t, f0, formants, breath=0.15, rng=None):
    """A voiced vowel: a glottal buzz shaped by resonances (each formant a frequency and a bandwidth)."""
    phase = 2 * np.pi * np.cumsum(f0) / RATE
    buzz = np.zeros(len(t))
    for k in range(1, 40):
        buzz += np.sin(k * phase) / k ** 1.1
    if rng is not None:
        buzz += breath * rng.normal(size=len(t))
    spectrum = np.fft.rfft(buzz)
    f = np.fft.rfftfreq(len(buzz), 1 / RATE)
    shape = sum(a * np.exp(-((f - fc) / bw) ** 2) for fc, bw, a in formants)
    return np.fft.irfft(spectrum * shape, n=len(buzz))


def murmur():
    """A crowd talking in a room somewhere, the words never quite clear."""
    rng = np.random.default_rng(203)
    n = int(4.0 * RATE)
    out = np.zeros(n)
    vowels = [((700, 120, 1), (1200, 150, 0.6)), ((400, 100, 1), (2000, 200, 0.5)), ((500, 100, 1), (900, 120, 0.6)), ((300, 80, 1), (2300, 250, 0.4))]
    for voice in range(6):
        base = rng.uniform(100, 210)
        at = rng.uniform(0, 0.4)
        while at < 3.6:
            length = rng.uniform(0.08, 0.25)
            t = seconds(length)
            f0 = base * (1 + 0.08 * np.sin(2 * np.pi * rng.uniform(1, 3) * t))
            syl = vowel(t, f0, vowels[rng.integers(len(vowels))], 0.1, rng) * np.sin(np.pi * t / length) ** 1.5
            place(out, syl * rng.uniform(0.4, 1), at)
            at += length + rng.uniform(0.02, 0.18) + (0.4 if rng.random() < 0.12 else 0)
    # Through a wall: the highs gone
    write("murmur", reverb(band(out, 120, 1400)), 0.5)


def squeak():
    """Rats: a few high, quick chirps."""
    rng = np.random.default_rng(204)
    out = np.zeros(int(1.2 * RATE))
    for at in np.sort(rng.uniform(0, 0.9, 5)):
        length = rng.uniform(0.04, 0.09)
        t = seconds(length)
        f = rng.uniform(3200, 4800) * (1 + 0.3 * np.sin(np.pi * t / length))
        chirp = np.sin(2 * np.pi * np.cumsum(f) / RATE) * np.sin(np.pi * t / length)
        place(out, chirp * rng.uniform(0.5, 1), at)
    write("squeak", reverb(out), 0.45)


def groan():
    """A long, low metal groan, as if the building settled."""
    rng = np.random.default_rng(205)
    t = seconds(3.0)
    f = 55 + 12 * np.sin(2 * np.pi * 0.35 * t) + 5 * np.sin(2 * np.pi * 1.7 * t)
    phase = 2 * np.pi * np.cumsum(f) / RATE
    tone = sum(np.sin(k * phase + rng.uniform(0, 6)) * a for k, a in ((1, 1), (2, 0.6), (3.01, 0.4), (4.97, 0.25), (7.1, 0.15)))
    grit = band(rng.normal(size=len(t)), 200, 1200) * 0.3
    env = np.sin(np.pi * t / t[-1]) ** 0.8
    write("groan", reverb((tone + grit) * env, decay=0.6), 0.6)


def drag():
    """Something heavy dragged a few feet across a concrete floor."""
    rng = np.random.default_rng(206)
    t = seconds(1.8)
    rough = band(rng.normal(size=len(t)), 120, 2200) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 9 * t)))
    env = np.clip(t / 0.15, 0, 1) * np.clip((1.6 - t) / 0.3, 0, 1)
    write("drag", reverb(rough * env), 0.55)


def cough():
    """Two dry coughs from somebody out of sight."""
    rng = np.random.default_rng(207)
    out = np.zeros(int(1.4 * RATE))
    for at, strength in ((0.05, 1.0), (0.5, 0.8)):
        t = seconds(0.3)
        burst = band(rng.normal(size=len(t)), 250, 3500) * np.exp(-t * 14) * np.clip(t / 0.01, 0, 1)
        voiced = vowel(t, 140 * (1 - 0.3 * t), ((550, 150, 1), (1600, 300, 0.5)), 0.4, rng) * np.exp(-t * 18)
        place(out, (burst + 0.6 * voiced / max(1e-9, np.max(np.abs(voiced)))) * strength, at)
    write("cough", reverb(out), 0.6)


def hello():
    """'Hello?': two syllables in a not-quite-human voice, rising at the end. A mimic's best attempt."""
    rng = np.random.default_rng(208)
    parts = []
    # "heh": a breath then an open e; "low": an o that rises into a question
    t1 = seconds(0.22)
    h = band(rng.normal(size=int(0.06 * RATE)), 600, 4000) * np.linspace(0, 1, int(0.06 * RATE)) * 0.4
    e = vowel(t1, 150 + 10 * t1, ((530, 90, 1), (1850, 160, 0.6), (2500, 200, 0.3)), 0.08, rng) * np.sin(np.pi * t1 / t1[-1]) ** 0.6
    t2 = seconds(0.42)
    o = vowel(t2, 140 + 110 * (t2 / t2[-1]) ** 2, ((450, 80, 1), (850, 110, 0.7), (2400, 200, 0.2)), 0.08, rng) * np.sin(np.pi * t2 / t2[-1]) ** 0.7
    l = vowel(seconds(0.05), np.full(int(0.05 * RATE), 145.0), ((350, 80, 1), (1100, 150, 0.4)), 0.05, rng)
    parts = [h, e, l * 0.6, o, np.zeros(int(0.3 * RATE))]
    out = np.concatenate([p / max(1e-9, np.max(np.abs(p))) * s for p, s in zip(parts, (0.3, 1, 0.6, 1, 0))])
    write("hello", reverb(band(out, 90, 3600), decay=0.5), 0.5)


def knock():
    """Three knocks on a door down the corridor."""
    rng = np.random.default_rng(209)
    out = np.zeros(int(1.6 * RATE))
    for at in (0.05, 0.33, 0.6):
        place(out, thud(0.18, rng.uniform(140, 170), rng, 0.8), at)
    write("knock", reverb(out), 0.6)


def slam():
    """A door slamming, somewhere in a house."""
    rng = np.random.default_rng(210)
    out = np.zeros(int(1.8 * RATE))
    place(out, thud(0.5, 60, rng, 1.0), 0.02)
    place(out, 0.5 * thud(0.3, 110, rng, 0.6), 0.03)
    write("slam", reverb(out, decay=0.5), 0.75)


def phone():
    """An old desk phone in another office, ringing once and stopping."""
    t = seconds(1.6)
    bell = (np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 480 * t)) * (np.sin(2 * np.pi * 20 * t) > 0)
    env = np.clip(t / 0.02, 0, 1) * np.clip((1.5 - t) / 0.05, 0, 1)
    write("phone", reverb(band(bell * env, 300, 2500)), 0.45)


def static():
    """A television left on in an empty house: a hiss that swells and cuts out."""
    rng = np.random.default_rng(211)
    t = seconds(2.5)
    hiss = band(rng.normal(size=len(t)), 800, 9000) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.7 * t) ** 2)
    hum = 0.15 * np.sin(2 * np.pi * 60 * t)
    env = np.clip(t / 0.4, 0, 1) * np.clip((2.4 - t) / 0.05, 0, 1)
    write("static", reverb((hiss + hum) * env), 0.4)


def wings():
    """Large soft wings beating close by: a Deathmoth."""
    rng = np.random.default_rng(212)
    t = seconds(1.5)
    flutter = band(rng.normal(size=len(t)), 80, 1200) * (0.3 + 0.7 * np.abs(np.sin(2 * np.pi * 11 * t)) ** 3)
    env = np.sin(np.pi * t / t[-1]) ** 0.6
    write("wings", flutter * env, 0.55)


def cowbell():
    """A cowbell somewhere in the fields, with no cow."""
    t = seconds(1.6)
    tone = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((540, 1), (800, 0.7), (1310, 0.3), (1820, 0.2))) * np.exp(-t * 5)
    out = tone + 0.5 * np.concatenate([np.zeros(int(0.45 * RATE)), tone[: len(t) - int(0.45 * RATE)]])
    write("cowbell", out, 0.4)


def caralarm():
    """A car alarm a few blocks over, whooping and then stopping."""
    t = seconds(3.0)
    f = 900 + 450 * (0.5 + 0.5 * np.sin(2 * np.pi * 2.2 * t))
    tone = np.sign(np.sin(2 * np.pi * np.cumsum(f) / RATE)) * 0.6
    env = np.clip(t / 0.05, 0, 1) * np.clip((2.9 - t) / 0.05, 0, 1)
    write("caralarm", reverb(band(tone * env, 400, 3000), decay=0.7), 0.35)


def smiler():
    """A Smiler: a thin, rising ring in the ears, and under it a slow, wet breath that sounds like a laugh."""
    rng = np.random.default_rng(213)
    t = seconds(2.8)
    ring = np.sin(2 * np.pi * (3400 + 300 * t / t[-1]) * t) * np.clip(t / 1.2, 0, 1) * np.clip((2.7 - t) / 0.4, 0, 1)
    breath = band(rng.normal(size=len(t)), 200, 1500) * (0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 3.3 * t)) ** 4) * np.exp(-((t - 1.6) / 0.7) ** 2)
    write("smiler", 0.35 * ring + breath, 0.55)


def grab():
    """A Duller's arm through the wall: plaster cracking, a thump, a scrape."""
    rng = np.random.default_rng(214)
    out = np.zeros(int(1.2 * RATE))
    crack = band(rng.normal(size=int(0.12 * RATE)), 1500, 8000) * np.exp(-seconds(0.12) * 30)
    place(out, crack, 0.0)
    place(out, thud(0.3, 75, rng, 0.9), 0.05)
    t = seconds(0.6)
    place(out, band(rng.normal(size=len(t)), 400, 3000) * np.exp(-t * 4) * 0.4, 0.25)
    write("grab", out, 0.8)


def ratscream():
    """The Screaming: a pack of Death Rats in full cry after something, squeals piling up into a shriek and breaking off."""
    rng = np.random.default_rng(311)
    out = np.zeros(int(2.8 * RATE))
    for i in range(46):
        at = rng.uniform(0, 2.2) ** 1.2 / 2.2 ** 0.2
        length = rng.uniform(0.08, 0.35)
        t = seconds(length)
        f0 = rng.uniform(1800, 3400) * (1 + 0.25 * at)
        f = f0 * (1 + 0.45 * np.sin(np.pi * t / length)) * (1 + 0.04 * np.sin(2 * np.pi * 38 * t))
        tone = np.sin(2 * np.pi * np.cumsum(f) / RATE) + 0.35 * np.sin(4 * np.pi * np.cumsum(f) / RATE)
        place(out, tone * np.sin(np.pi * t / length) ** 0.6 * rng.uniform(0.4, 1) * (0.5 + at / 2.2), at)
    rasp = band(rng.normal(size=len(out)), 1500, 6000) * 0.12 * np.clip(np.linspace(-0.2, 1.2, len(out)), 0, 1)
    write("ratscream", reverb(out + rasp, decay=0.5), 0.6)


def rumble():
    """One of the Mangled's steps, far off: a deep impact that is felt more than heard, and the ground settling after."""
    rng = np.random.default_rng(312)
    t = seconds(2.2)
    hit = np.sin(2 * np.pi * (34 - 8 * t) * t) * np.exp(-t * 3.2)
    under = band(rng.normal(size=len(t)), 20, 140) * np.exp(-t * 1.6) * 1.4
    creak = band(rng.normal(size=len(t)), 300, 900) * np.exp(-((t - 0.5) ** 2) / 0.05) * 0.15
    write("rumble", reverb(hit + under + creak, decay=0.6), 0.85)


def chorus():
    """The Mangled close by: many voices at once, none of them saying anything you can follow, over each other."""
    rng = np.random.default_rng(313)
    t = seconds(3.5)
    out = np.zeros(len(t))
    vowels = ((700, 1200, 2500), (300, 2300, 3000), (450, 900, 2500), (500, 1700, 2500), (350, 800, 2300))
    for i in range(14):
        start, length = rng.uniform(0, 2.5), rng.uniform(0.4, 1.2)
        seg = seconds(length)
        f0 = rng.uniform(95, 260)
        formants = [(f, f * 0.12, a) for f, a in zip(vowels[rng.integers(len(vowels))], (1.0, 0.7, 0.35))]
        v = vowel(seg, f0 * (1 + 0.15 * np.sin(2 * np.pi * rng.uniform(0.5, 2) * seg)), formants, breath=0.3, rng=rng)
        place(out, v * np.sin(np.pi * seg / length) * rng.uniform(0.3, 1), start)
    write("chorus", reverb(band(out, 80, 3800), decay=0.65), 0.55)


def howl():
    """The Bacteria: a long, inhuman howl, a voice and something electrical in the same throat, wavering and breaking
    up as if the line were bad, and cut off short."""
    rng = np.random.default_rng(314)
    t = seconds(2.6)
    f0 = 210 + 260 * np.clip(t / 0.5, 0, 1) - 90 * np.clip((t - 1.4) / 1.0, 0, 1) + 18 * np.sin(2 * np.pi * 6.5 * t)
    voice = vowel(t, f0, ((650, 90, 1.0), (1100, 120, 0.7), (2600, 200, 0.35)), breath=0.25, rng=rng)
    # The same pitch a fifth up and detuned, so it never quite sounds like one throat
    whine = np.sin(2 * np.pi * np.cumsum(f0 * 1.51) / RATE) * 0.25
    out = voice / max(1e-9, np.max(np.abs(voice))) + whine
    # Crushed and gated in ragged stretches, as through a dying speaker
    crushed = np.round(out * 6) / 6
    gate = np.repeat(rng.uniform(0, 1, len(t) // 1500 + 1) > 0.12, 1500)[: len(t)]
    out = np.where(gate, 0.6 * out + 0.4 * crushed, 0.15 * out)
    out *= np.clip(t / 0.08, 0, 1) * np.clip((2.45 - t) / 0.05, 0, 1)
    write("howl", reverb(band(out, 120, 6000), decay=0.6), 0.7)


def gurgle():
    """A Wretch close by: a wet, slow gurgle in a throat with no lips to shape it, and a click of teeth."""
    rng = np.random.default_rng(315)
    t = seconds(1.8)
    f0 = 85 + 20 * np.sin(2 * np.pi * 0.7 * t) + 10 * rng.normal(size=len(t)).cumsum() / np.sqrt(len(t))
    voice = vowel(t, f0, ((400, 120, 1.0), (850, 160, 0.6), (2300, 300, 0.2)), breath=0.5, rng=rng)
    # Bubbling: the voice choked off and let go a dozen times a second
    bubbles = 0.35 + 0.65 * np.abs(np.sin(2 * np.pi * (9 + 3 * np.sin(2 * np.pi * 0.9 * t)) * t)) ** 3
    out = voice * bubbles * np.sin(np.pi * t / t[-1]) ** 0.5
    place(out, band(rng.normal(size=int(0.03 * RATE)), 2000, 7000) * np.exp(-seconds(0.03) * 150) * 2, 1.45)
    write("gurgle", band(out, 60, 5000), 0.6)


def snarl():
    """A Wretch turning on you: a rasping, rising snarl through bare teeth."""
    rng = np.random.default_rng(316)
    t = seconds(1.2)
    f0 = 140 + 160 * np.clip(t / 0.35, 0, 1) + 25 * np.sin(2 * np.pi * 31 * t)
    voice = vowel(t, f0, ((800, 150, 1.0), (1500, 200, 0.8), (3000, 400, 0.4)), breath=1.2, rng=rng)
    rasp = band(rng.normal(size=len(t)), 1500, 6000) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 31 * t)))
    out = (voice / max(1e-9, np.max(np.abs(voice))) + 0.5 * rasp) * np.clip(t / 0.05, 0, 1) * np.clip((1.15 - t) / 0.3, 0, 1)
    write("snarl", reverb(out, decay=0.3), 0.75)


def _click(rng, length=0.012, lo=1800, hi=7000):
    """One dry click of chitin on chitin."""
    t = seconds(length)
    return band(rng.normal(size=len(t)), lo, hi) * np.exp(-t * 600)


def chitter():
    """A Giant Spider unseen in the dark: its mouthparts clicking in quick runs, with a dry rattle under them."""
    rng = np.random.default_rng(401)
    out = np.zeros(int(1.6 * RATE))
    at = 0.05
    for burst in range(3):
        n = int(rng.integers(5, 10))
        for _ in range(n):
            place(out, _click(rng) * rng.uniform(0.5, 1.0), at)
            at += rng.uniform(0.025, 0.05)
        at += rng.uniform(0.12, 0.25)
    t = seconds(len(out) / RATE)
    rattle = band(rng.normal(size=len(t)), 900, 3200) * 0.08 * (0.5 + 0.5 * np.sin(2 * np.pi * 38 * t)) * np.clip(np.sin(np.pi * t / t[-1]), 0, 1)
    write("chitter", reverb(out + rattle, decay=0.4), 0.6)


def spiderhiss():
    """A Giant Spider rearing: a harsh hiss forced out with a rasp of stridulation through it, and a clack at its end."""
    rng = np.random.default_rng(402)
    t = seconds(1.1)
    env = np.clip(t / 0.08, 0, 1) * np.clip((1.05 - t) / 0.4, 0, 1)
    hiss = band(rng.normal(size=len(t)), 2200, 9000) * env
    rasp = band(rng.normal(size=len(t)), 500, 2500) * (0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 55 * t))) * env * 0.7
    out = hiss + rasp
    place(out, _click(rng, 0.02, 800, 5000) * 3, 0.98)
    write("spiderhiss", reverb(out, decay=0.3), 0.75)


def spiderbite():
    """The bite: a wet crunch as the fangs go in, and the click of them closing."""
    rng = np.random.default_rng(403)
    out = np.zeros(int(0.5 * RATE))
    place(out, _click(rng, 0.02, 600, 6000) * 2.5, 0.0)
    t = seconds(0.25)
    place(out, band(rng.normal(size=len(t)), 200, 1800) * np.exp(-t * 18) * 0.9, 0.02)
    place(out, _click(rng, 0.015) * 1.5, 0.2)
    write("spiderbite", out, 0.8)


def skitter():
    """Many legs on rock somewhere off in the caves: a run of light, quick taps that comes and goes."""
    rng = np.random.default_rng(404)
    out = np.zeros(int(2.2 * RATE))
    at = 0.05
    while at < 1.9:
        k = np.sin(np.pi * at / 2.0)
        place(out, _click(rng, 0.008, 1200, 5000) * rng.uniform(0.3, 1.0) * k, at)
        place(out, thud(0.03, rng.uniform(150, 260), rng, 0.2) * 0.25 * k, at)
        at += rng.uniform(0.018, 0.06)
    write("skitter", reverb(out, decay=0.5), 0.55)


def spiderhurt():
    """Struck: a shrill rasping squeal, short, and a burst of clicks."""
    rng = np.random.default_rng(405)
    t = seconds(0.6)
    f = 1400 + 600 * np.sin(np.pi * t / 0.6)
    tone = np.sin(2 * np.pi * np.cumsum(f) / RATE) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 70 * t)))
    out = (0.5 * tone + band(rng.normal(size=len(t)), 2000, 8000) * 0.6) * np.clip(t / 0.02, 0, 1) * np.clip((0.6 - t) / 0.3, 0, 1)
    for i in range(6):
        place(out, _click(rng) * 0.8, 0.3 + i * 0.03)
    write("spiderhurt", reverb(out, decay=0.3), 0.7)


def spiderdeath():
    """Dying: a long falling hiss and rasp, legs scraping, a last few slow clicks."""
    rng = np.random.default_rng(406)
    t = seconds(2.0)
    env = np.clip(t / 0.05, 0, 1) * np.exp(-t * 1.6)
    rasp = band(rng.normal(size=len(t)), 400, 3000) * (0.4 + 0.6 * np.abs(np.sin(2 * np.pi * (60 - 25 * t) * t))) * env
    hiss = band(rng.normal(size=len(t)), 2500, 8000) * env * 0.6
    out = rasp + hiss
    for at in (1.1, 1.4, 1.75):
        place(out, _click(rng, 0.015) * 0.6, at)
    write("spiderdeath", reverb(out, decay=0.45), 0.7)


SPIDER = (chitter, spiderhiss, spiderbite, skitter, spiderhurt, spiderdeath)


def main():
    for spider in SPIDER:
        spider()
    howl()
    gurgle()
    snarl()
    ratscream()
    rumble()
    chorus()
    footsteps()
    scratch()
    murmur()
    squeak()
    groan()
    drag()
    cough()
    hello()
    knock()
    slam()
    phone()
    static()
    wings()
    cowbell()
    caralarm()
    smiler()
    grab()


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["spider"]:
        for spider in SPIDER:
            spider()
    else:
        main()
