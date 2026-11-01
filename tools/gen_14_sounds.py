"""Level 14, "The Hospital" (experimental): the level's sound bed and the sounds of its rules (sounds/ambient/14/). All
synthesised, mono OGG. Loops are seamless: noise is shaped over the whole loop with the FFT (so it is circular), every
tone has a whole number of cycles in the loop, and events are laid in wrapping round its end.

Loops (src/AtmosphereSystem.L14.cs):
    air         the hospital's air: a low ventilation drone, a duct's resonance, the mains far off (everywhere; quieter
                where the lights are dead)
    buzz        a failing fluorescent tube: the 120 Hz buzz, stuttering out and back with the starter's tick (where the
                lights are on)
    ward        the inpatient rooms' bright, clean hum ("all a blinding white shade")
    monitor     a heart monitor's slow beep, 48 a minute (the wards; loudest in intensive care)
    torture     the torture chambers: blood dripping, chains creaking, something low and wet (heard from near the door too)
    contam      a contaminated room: a Geiger counter's crackle over a hiss
    dread       the Hunter near: a sub-bass pressure the game swells as it comes
    heartbeat   your own heart in your ears (the game raises its pitch, and so its pace, with the dread)
One-shots somewhere off in the halls every 10 to 30 s ("the constant sound of distant footsteps and whispers"):
    steps1 (slow footsteps down a hall), steps2 (a shuffling pair), door (a door opening and swinging shut), whisper1,
    whisper2 (whispering, never a word clear: one voice, two), gurney (a gurney's squeaking wheel going by), beeps (a
    monitor's alarm far off), chime (the PA's chime, and an announcement nobody can make out)
Effects (src/Regions/L14System.cs):
    spark (equipment shorting out), clatter (instruments flying off a trolley), creak (the floor giving a little under
    you), latch (a reception room's door that will not let you back in)

Run from the repo root:  python tools/gen_14_sounds.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from gen_entity_sounds import RATE, band, place, thud  # noqa: E402
from oggutil import write_ogg  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "assets", "backrooms", "sounds", "ambient", "14")
WRITTEN = []


def write(name, sig, peak, fade=True):
    """Normalises to `peak` and writes an OGG (short fades at the ends of one-shots so nothing clicks; loops get none)."""
    sig = np.array(sig, dtype=np.float64)
    n = min(len(sig) // 4, int(0.01 * RATE))
    if fade and n > 0:
        sig[:n] *= np.linspace(0, 1, n)
        sig[-n:] *= np.linspace(1, 0, n)
    sig = peak * sig / max(1e-9, np.max(np.abs(sig)))
    path = os.path.join(OUT, name + ".ogg")
    if write_ogg(path, sig, RATE):
        print("wrote", os.path.relpath(path, ROOT))
    WRITTEN.append(name)


# ======================= Helpers =======================

def norm(x):
    return x / max(1e-9, np.max(np.abs(x)))


def times(length):
    return np.arange(int(length * RATE)) / RATE


def periodic_noise(rng, n, shape_fn):
    """Noise of n samples with the spectrum shape_fn(f), circular (it loops without a seam)."""
    f = np.fft.rfftfreq(n, 1 / RATE)
    spectrum = (rng.normal(size=len(f)) + 1j * rng.normal(size=len(f))) * shape_fn(f)
    spectrum[0] = 0
    return norm(np.fft.irfft(spectrum, n=n))


def shaped(x, peaks):
    """x through resonances: peaks are (centre, width, gain)."""
    f = np.fft.rfftfreq(len(x), 1 / RATE)
    shape = sum(a * np.exp(-((f - fc) / bw) ** 2) for fc, bw, a in peaks)
    return np.fft.irfft(np.fft.rfft(x) * shape, n=len(x))


def wrap_place(out, sound, at):
    """Adds sound into a loop at `at` seconds, wrapping round its end."""
    i = int(at * RATE) % len(out)
    first = min(len(sound), len(out) - i)
    out[i:i + first] += sound[:first]
    if len(sound) > first:
        out[:len(sound) - first] += sound[first:]


def circ_smooth(x, ms):
    """A circular moving average over `ms` milliseconds (softens a loop's envelope without a seam)."""
    k = max(1, int(ms / 1000 * RATE))
    kernel = np.zeros(len(x))
    kernel[:k] = 1.0 / k
    return np.fft.irfft(np.fft.rfft(x) * np.fft.rfft(kernel), n=len(x))


def stickslip(n, rate, peaks, rng, jitter=0.25):
    """Friction: impulses at `rate` (Hz, per sample) through resonances: a creak, a squeak, a chain's links grinding."""
    phase = np.cumsum(rate) / RATE
    idx = np.where(np.diff(np.floor(phase)) > 0)[0]
    x = np.zeros(n)
    x[idx] = rng.uniform(1 - jitter, 1.0, len(idx))
    return shaped(x, peaks)


def ring(length, partials, rng, click=0.4):
    """A struck bit of metal: inharmonic partials (frequency, amplitude, decay per second) and a click."""
    t = times(length)
    out = sum(a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t * d) for f, a, d in partials)
    out += click * band(rng.normal(size=len(t)), 2000, 12000) * np.exp(-t * 400)
    return out * np.minimum(1, t / 0.0007)


def hall(sig, rng, length=1.6, decay=0.45, wet=0.6, lo=150, hi=3200, pre=0.025):
    """A long, hard hospital corridor: the sound's tail rolling on down it (an FFT convolution with decaying noise)."""
    kn = int(length * RATE)
    tk = np.arange(kn) / RATE
    kernel = band(rng.normal(size=kn) * np.exp(-tk / decay), lo, hi)
    kernel[:int(pre * RATE)] = 0
    size = len(sig) + kn
    tail = np.fft.irfft(np.fft.rfft(sig, size) * np.fft.rfft(kernel, size), size)
    out = np.zeros(size)
    out[:len(sig)] += sig
    # (The tail carries wet^2 of the dry sound's energy, spread over its length)
    out += wet * tail * np.sqrt(np.sum(sig ** 2) / max(1e-12, np.sum(tail ** 2)))
    # Trim the silence at the end
    loud = np.where(np.abs(out) > 0.004 * np.max(np.abs(out)))[0]
    return out[: (loud[-1] + 1 if len(loud) else size)]


def far(sig, rng, lo=120, hi=2800, **kw):
    """Somewhere off down the halls: the highs gone, and the hall's tail."""
    return hall(band(sig, lo, hi), rng, **kw)


def env_ar(t, attack, release, length):
    return np.minimum(1, t / attack) * np.clip((length - t) / release, 0, 1)


# ======================= Loops =======================

def air(rng):
    """The hospital's air: a ventilation drone (brown noise rolled off at 900 Hz), the duct's 95 Hz resonance, a thin hiss
    from the grilles, the mains far off; a slow swell, three in the 12 s loop."""
    n = 12 * RATE
    t = np.arange(n) / RATE
    drone = periodic_noise(rng, n, lambda f: 1 / np.maximum(f, 30) ** 1.2 * np.exp(-(f / 900) ** 2))
    duct = periodic_noise(rng, n, lambda f: np.exp(-((f - 95) / 6) ** 2) + 0.5 * np.exp(-((f - 190) / 10) ** 2))
    hiss = periodic_noise(rng, n, lambda f: np.exp(-((f - 2500) / 1500) ** 2))
    mains = 0.10 * np.sin(2 * np.pi * 60 * t) + 0.05 * np.sin(2 * np.pi * 120 * t + 1) + 0.02 * np.sin(2 * np.pi * 180 * t + 2)
    swell = 1 + 0.12 * np.sin(2 * np.pi * t / 4)
    return (0.8 * drone + 0.35 * duct + 0.05 * hiss) * swell + mains


def buzz(rng):
    """A failing fluorescent tube: a 120 Hz buzz rich in harmonics with the ballast's fizz; five times in the 8 s loop it
    drops out for a moment and comes back with the starter's tick."""
    n = 8 * RATE
    t = np.arange(n) / RATE
    tone = sum(np.sin(2 * np.pi * 120 * k * t + rng.uniform(0, 6)) / k ** 1.2 for k in range(1, 40) if 120 * k < 6000)
    fizz = periodic_noise(rng, n, lambda f: np.exp(-((f - 3500) / 2000) ** 2)) * (0.5 + 0.5 * np.sin(2 * np.pi * 120 * t)) ** 4
    env = np.ones(n)
    clicks = np.zeros(n)
    for at in np.sort(rng.uniform(0, 8, 5)):
        for _ in range(int(rng.integers(1, 4))):
            i, L = int(at * RATE), int(rng.uniform(0.03, 0.2) * RATE)
            idx = np.arange(i, i + L) % n
            env[idx] = rng.uniform(0.03, 0.25)
            tick = norm(band(rng.normal(size=int(0.004 * RATE)), 1000, 7000)) * np.exp(-times(0.004) * 900)
            wrap_place(clicks, tick * rng.uniform(0.4, 0.8), (i + L) / RATE)
            at += (L / RATE) + rng.uniform(0.04, 0.12)
    env = circ_smooth(env, 4)
    return (0.6 * norm(tone) + 0.25 * fizz) * env + 0.5 * clicks


def ward(rng):
    """The inpatient rooms' bright hum: the tubes' clean upper harmonics over a soft high air, a slow shimmer (10 s)."""
    n = 10 * RATE
    t = np.arange(n) / RATE
    tone = (0.35 * np.sin(2 * np.pi * 120 * t) + 0.7 * np.sin(2 * np.pi * 240 * t + 0.4) + 0.4 * np.sin(2 * np.pi * 360 * t + 1.1)
            + 0.3 * np.sin(2 * np.pi * 480 * t + 2.0) + 0.06 * np.sin(2 * np.pi * 1920 * t) + 0.03 * np.sin(2 * np.pi * 3840 * t + 0.5))
    shimmer = 1 + 0.08 * np.sin(2 * np.pi * 0.1 * t)
    high = periodic_noise(rng, n, lambda f: np.exp(-((f - 6000) / 4000) ** 2))
    return tone * shimmer + 0.06 * high


def monitor(rng):
    """A heart monitor's slow beep: eight in the 10 s loop (48 a minute), each a soft 960 Hz tone, a little room echo."""
    n = 10 * RATE
    out = np.zeros(n)
    t = times(0.11)
    beep = (np.sin(2 * np.pi * 960 * t) + 0.15 * np.sin(2 * np.pi * 2880 * t)) * env_ar(t, 0.003, 0.02, 0.11)
    for k in range(8):
        at = 0.2 + k * 1.25
        wrap_place(out, beep, at)
        for d, g in ((0.017, 0.25), (0.031, 0.15), (0.052, 0.08)):
            wrap_place(out, beep * g, at + d)
    return out


def drip(rng):
    """A drop falling into a pool on the marble: a plink rising as the bubble closes, a tiny tap."""
    t = times(0.3)
    f0 = rng.uniform(900, 1600)
    f = f0 * (1 + 0.7 * (1 - np.exp(-t * 45)))
    plink = np.sin(2 * np.pi * np.cumsum(f) / RATE) * np.exp(-t * rng.uniform(18, 30))
    tap = band(rng.normal(size=len(t)), 300, 2500) * np.exp(-t * 300) * 0.4
    out = plink + tap
    for d, g in ((0.021, 0.3), (0.043, 0.18), (0.07, 0.1)):
        place(out, plink * g, d)
    return out


def chain_creak(rng, length):
    """Chains swaying from a hook: links grinding (stick-slip through a metal ring's resonances) and a clink or two."""
    n = int(length * RATE)
    t = np.arange(n) / RATE
    walk = np.cumsum(rng.normal(size=n)) / np.sqrt(RATE) * 30
    rate = np.clip(45 + walk - np.linspace(walk[0], walk[-1], n), 18, 110)
    grind = stickslip(n, rate, [(720, 90, 1.0), (1350, 140, 0.7), (2600, 260, 0.35)], rng)
    out = norm(grind) * np.sin(np.pi * t / length) ** 1.5
    for at in rng.uniform(0.1, length - 0.2, int(rng.integers(1, 3))):
        base = rng.uniform(1900, 3200)
        place(out, 0.6 * ring(0.4, [(base, 1.0, 22), (base * 1.47, 0.6, 30), (base * 2.31, 0.35, 40), (base * 3.2, 0.2, 55)], rng), at)
    return out


def wet(rng, length):
    """Something low and wet: a slow gurgling squelch."""
    n = int(length * RATE)
    t = np.arange(n) / RATE
    body = band(rng.normal(size=n), 60, 520)
    fm = 5 + 7 * t / length
    gurgle = (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(fm) / RATE)) ** 2
    blob = shaped(rng.normal(size=n), [(180, 60, 1.0), (420, 90, 0.5)])
    return (norm(body) * gurgle + 0.5 * norm(blob) * gurgle ** 2) * np.sin(np.pi * t / length) ** 2


def torture(rng):
    """The torture chambers (16 s): a low room tone, blood dripping now near and now further, the chains creaking, and
    twice something low and wet."""
    n = 16 * RATE
    room = periodic_noise(rng, n, lambda f: 1 / np.maximum(f, 20) ** 1.5 * np.exp(-(f / 400) ** 2))
    out = 0.2 * room
    at = 0.3
    while at < 15.8:
        wrap_place(out, drip(rng) * rng.uniform(0.25, 0.7), at)
        at += rng.uniform(1.1, 3.0)
    for at in (1.5, 6.8, 11.9):
        wrap_place(out, 0.45 * chain_creak(rng, rng.uniform(0.9, 1.6)), at + rng.uniform(-0.4, 0.4))
    for at in (4.2, 13.4):
        wrap_place(out, 0.55 * wet(rng, rng.uniform(0.7, 1.1)), at)
    return out


def contam(rng):
    """A contaminated room (8 s): a Geiger counter's ticks, now sparse, now in bursts, over a faint hiss."""
    n = 8 * RATE
    t = np.arange(n) / RATE
    hiss = periodic_noise(rng, n, lambda f: np.exp(-((f - 5000) / 3500) ** 2)) * (1 + 0.25 * np.sin(2 * np.pi * t / 4))
    out = 0.2 * hiss
    tick_t = times(0.004)
    at = 0.0
    while at < 8:
        rate = 5 + 4 * np.sin(2 * np.pi * at / 4) + (25 if (at % 4) > 2.6 and (at % 4) < 3.0 else 0)
        at += rng.exponential(1 / max(1.0, rate))
        if at >= 8:
            break
        tick = (np.sin(2 * np.pi * rng.uniform(2200, 3200) * tick_t) * np.exp(-tick_t * 1800)
                + band(rng.normal(size=len(tick_t)), 1500, 12000) * np.exp(-tick_t * 2500))
        wrap_place(out, tick * rng.uniform(0.7, 1.0), at)
    return out


def dread(rng):
    """The Hunter near (12 s): two sub-bass tones beating 1.5 times a second (a pressure that pulses), their overtones so
    a small speaker carries them, a rumble, and very faint, two high tones grinding against each other."""
    n = 12 * RATE
    t = np.arange(n) / RATE
    sub = np.sin(2 * np.pi * 33 * t) + 0.8 * np.sin(2 * np.pi * 34.5 * t + 1)
    over = 0.35 * np.sin(2 * np.pi * 66 * t) + 0.2 * np.sin(2 * np.pi * 99 * t + 0.4) + 0.12 * np.sin(2 * np.pi * 69 * t + 2)
    rumble = periodic_noise(rng, n, lambda f: np.exp(-((f - 45) / 25) ** 2))
    whine = 0.02 * (np.sin(2 * np.pi * 2217 * t) + np.sin(2 * np.pi * 2229.5 * t))
    swell = 0.75 + 0.25 * np.sin(2 * np.pi * t / 6)
    return (0.6 * sub + over + 0.6 * rumble) * swell + whine


def heartbeat(rng):
    """Your own heart (10 s): twelve beats (72 a minute), lub and dub, muffled as if heard from inside."""
    n = 10 * RATE
    out = np.zeros(n)
    for k in range(12):
        at = k * 10 / 12
        lub = band(thud(0.2, 52, rng, 0.25), 20, 260) * env_ar(times(0.2), 0.004, 0.03, 0.2)
        dub = band(thud(0.16, 68, rng, 0.2), 20, 300) * env_ar(times(0.16), 0.004, 0.03, 0.16) * 0.65
        wrap_place(out, lub, at + 0.1)
        wrap_place(out, dub, at + 0.37)
    blood = periodic_noise(rng, n, lambda f: np.exp(-((f - 70) / 40) ** 2)) * 0.05
    return out + blood


# ======================= Far off in the halls =======================

def step_sound(rng, heavy=True):
    """A hard shoe on vinyl: the heel's knock and its click."""
    s = thud(0.22, rng.uniform(80, 100), rng, 0.9 if heavy else 0.5)
    t = times(0.22)
    s += band(rng.normal(size=len(t)), 1500, 6000) * np.exp(-t * 140) * 0.5
    return s


def steps1(rng):
    """Slow footsteps down a hall: six, a little nearer then further, the last one a beat late."""
    out = np.zeros(int(5.0 * RATE))
    at = 0.1
    for i in range(6):
        gain = np.sin(np.pi * (i + 0.6) / 6.6) * rng.uniform(0.85, 1.0)
        place(out, step_sound(rng) * gain, at)
        at += rng.uniform(0.74, 0.84) + (0.35 if i == 4 else 0)
    return far(out, rng, length=1.8, decay=0.55, wet=0.7)


def scuff(rng):
    L = rng.uniform(0.13, 0.22)
    t = times(L)
    s = norm(band(rng.normal(size=len(t)), 300, 2400)) * np.sin(np.pi * t / L) ** 1.3
    s += 0.4 * thud(L, rng.uniform(70, 90), rng, 0.2)[: len(t)]
    return s


def steps2(rng):
    """A shuffling pair: two people's dragging steps, out of step with each other."""
    out = np.zeros(int(4.5 * RATE))
    for every, start, gain in ((0.62, 0.05, 1.0), (0.71, 0.3, 0.8)):
        at = start
        while at < 4.1:
            place(out, scuff(rng) * gain * rng.uniform(0.6, 1.0), at)
            at += every * rng.uniform(0.9, 1.15)
    return far(out, rng, lo=150, hi=3000, length=1.6, decay=0.5, wet=0.65)


def door(rng):
    """A door down the hall: the latch, the hinges creaking open, a pause, and it swings shut with a rattle."""
    out = np.zeros(int(2.8 * RATE))
    place(out, ring(0.15, [(2900, 0.6, 60), (4300, 0.4, 80)], rng, 0.8), 0.05)
    n = int(1.0 * RATE)
    tt = np.arange(n) / RATE
    rate = 160 + 260 * np.sin(np.pi * np.clip(tt / 1.0, 0, 1)) ** 0.7
    creak = stickslip(n, rate, [(950, 120, 1.0), (1900, 180, 0.6), (2850, 260, 0.3)], rng)
    place(out, 0.6 * norm(creak) * np.sin(np.pi * tt / 1.0) ** 0.8, 0.25)
    place(out, 1.2 * thud(0.35, 68, rng, 0.6), 1.85)
    for k in range(4):
        place(out, ring(0.06, [(rng.uniform(1500, 3000), 0.5, 90)], rng, 0.5) * 0.4, 1.88 + 0.03 * k + rng.uniform(0, 0.01))
    return far(out, rng, length=1.8, decay=0.5, wet=0.7)


WHISPER_VOWELS = [[(700, 160, 1.0), (1200, 200, 0.7), (2600, 300, 0.3)], [(400, 120, 1.0), (2000, 260, 0.6), (2800, 300, 0.3)],
                  [(500, 120, 1.0), (900, 160, 0.7), (2500, 300, 0.2)], [(300, 90, 1.0), (2300, 260, 0.6), (3000, 300, 0.3)],
                  [(600, 140, 1.0), (1000, 180, 0.6), (2400, 280, 0.25)]]


def whisper_voice(rng, length, pitch=1.0):
    """One voice whispering: words of two to four syllables, breathy vowels and hissed s's and sh's, never a word clear."""
    n = int(length * RATE)
    out = np.zeros(n)
    at = rng.uniform(0, 0.15)
    while at < length - 0.3:
        for _ in range(int(rng.integers(2, 5))):
            if rng.random() < 0.3:
                L = rng.uniform(0.06, 0.15)
                t = times(L)
                lo, hi = (3500, 9000) if rng.random() < 0.5 else (1800, 5000)
                syl = norm(band(rng.normal(size=len(t)), lo, hi)) * np.sin(np.pi * t / L) ** 1.5 * 0.6
            else:
                L = rng.uniform(0.08, 0.22)
                t = times(L)
                formants = [(f * pitch, bw, a) for f, bw, a in WHISPER_VOWELS[rng.integers(len(WHISPER_VOWELS))]]
                syl = norm(shaped(rng.normal(size=len(t)), formants)) * np.sin(np.pi * t / L) ** 1.2
            place(out, syl * rng.uniform(0.5, 1.0), at)
            at += L + rng.uniform(0.01, 0.06)
        at += rng.uniform(0.12, 0.4)
    return out


def whisper(rng, voices):
    """Whispering somewhere close by and yet not here: one voice, or two over each other."""
    length = 3.2
    out = whisper_voice(rng, length, 1.0)
    if voices > 1:
        out = out + 0.75 * np.roll(whisper_voice(rng, length, 0.85), int(0.35 * RATE))
    return hall(band(out, 300, 7000), rng, length=1.2, decay=0.35, wet=0.55, lo=300, hi=5000)


def gurney(rng):
    """A gurney going by somewhere: its wheels rumbling, one squeaking every turn, the frame rattling."""
    length = 4.2
    n = int(length * RATE)
    t = np.arange(n) / RATE
    swell = np.sin(np.pi * t / length) ** 2
    out = 0.35 * norm(band(rng.normal(size=n), 60, 400)) * swell
    at = 0.2
    while at < length - 0.2:
        L = rng.uniform(0.1, 0.16)
        tt = times(L)
        f = rng.uniform(1900, 2300) * (1 + 0.04 * np.sin(2 * np.pi * 28 * tt))
        ph = 2 * np.pi * np.cumsum(f) / RATE
        sq = (np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)) * np.sin(np.pi * tt / L) ** 0.8
        place(out, sq * 0.5 * swell[min(n - 1, int(at * RATE))], at)
        at += rng.uniform(0.52, 0.6)
    k = 0.0
    while k < length:
        k += rng.exponential(1 / 14)
        if k < length:
            place(out, ring(0.04, [(rng.uniform(2000, 5000), 0.3, 120)], rng, 0.4) * 0.3 * swell[min(n - 1, int(k * RATE))], k)
    return far(out, rng, lo=100, hi=3500, length=1.6, decay=0.5, wet=0.6)


def beeps(rng):
    """A monitor's alarm far off down the halls: three beeps and two, a high-priority alarm nobody comes to."""
    out = np.zeros(int(2.0 * RATE))
    t = times(0.15)
    tone = (np.sin(2 * np.pi * 880 * t) + 0.3 * np.sin(2 * np.pi * 2640 * t)) * env_ar(t, 0.004, 0.02, 0.15)
    for at in (0.05, 0.27, 0.49, 1.05, 1.27):
        place(out, tone, at)
    return far(out, rng, lo=300, hi=3500, length=2.0, decay=0.6, wet=0.8)


def chime(rng):
    """The PA's chime, three notes falling, and after it an announcement through a bad speaker that nobody can make out."""
    out = np.zeros(int(5.0 * RATE))
    for at, f0 in ((0.05, 659.25), (0.6, 523.25), (1.15, 392.0)):
        place(out, ring(1.4, [(f0, 1.0, 2.2), (f0 * 4, 0.25, 6), (f0 * 9.8, 0.08, 12)], rng, 0.05), at)
    n = int(2.6 * RATE)
    tt = np.arange(n) / RATE
    voice = np.zeros(n)
    at = 0.0
    while at < 2.4:
        L = rng.uniform(0.09, 0.22)
        t = times(L)
        f0 = 150 * (1 + 0.15 * np.sin(2 * np.pi * 0.7 * (at + t))) * (1 - 0.1 * t / L)
        formants = [(f, bw * 1.5, a) for f, bw, a in WHISPER_VOWELS[rng.integers(len(WHISPER_VOWELS))]]
        phase = 2 * np.pi * np.cumsum(f0) / RATE
        buzz_ = sum(np.sin(k * phase) / k for k in range(1, 30))
        syl = norm(shaped(buzz_, formants)) * np.sin(np.pi * t / L) ** 1.4
        place(voice, syl * rng.uniform(0.6, 1.0), at)
        at += L + rng.uniform(0.02, 0.07) + (0.25 if rng.random() < 0.15 else 0)
    voice = np.tanh(3 * band(voice, 450, 2600)) * np.sin(np.pi * np.clip(tt / 2.6, 0, 1)) ** 0.3
    place(out, 0.45 * voice, 2.0)
    return far(out, rng, lo=200, hi=3500, length=2.4, decay=0.7, wet=0.9)


# ======================= The rules' sounds =======================

def spark(rng):
    """Equipment shorting out: a crackle of sparks, the mains buzzing through something it shouldn't, a fizz."""
    length = 1.0
    n = int(length * RATE)
    t = np.arange(n) / RATE
    out = np.zeros(n)
    at = 0.0
    while at < 0.85:
        at += rng.exponential(1 / (300 * np.exp(-at * 2.5) + 20))
        place(out, norm(band(rng.normal(size=int(0.002 * RATE)), 1500, 14000)) * rng.uniform(0.3, 1.0) * np.exp(-at * 2.5), at)
    zap = np.sign(np.sin(2 * np.pi * 100 * t)) * 0.5 + np.sin(2 * np.pi * 50 * t)
    out += 0.35 * np.tanh(2 * zap) * np.exp(-t * 7) * (t < 0.35)
    out += 0.3 * norm(band(rng.normal(size=n), 3000, 10000)) * np.exp(-t * 5)
    return out


def clatter(rng):
    """Instruments flying off a trolley: a whoosh, then scalpels and a tray landing and bouncing on the floor."""
    out = np.zeros(int(1.4 * RATE))
    t = times(0.18)
    out[: len(t)] += 0.3 * norm(band(rng.normal(size=len(t)), 800, 5000)) * np.sin(np.pi * t / 0.18) ** 2
    for k, at in enumerate((0.18, 0.29, 0.36, 0.5, 0.58, 0.74, 0.86)):
        base = rng.uniform(2000, 4500)
        g = 1.0 / (1 + 0.35 * k)
        place(out, g * ring(0.35, [(base, 1.0, 28), (base * 1.48, 0.6, 35), (base * 2.31, 0.4, 45), (base * 0.53, 0.3, 20)], rng, 0.6), at)
    place(out, 0.7 * ring(0.6, [(820, 1.0, 8), (1310, 0.6, 10), (2210, 0.4, 14)], rng, 0.4), 0.33)  # the tray
    return out


def creak(rng):
    """The floor giving a little under you: a low groan of the boards under the tiles, a crackle of tile, a soft drop."""
    n = int(1.3 * RATE)
    t = np.arange(n) / RATE
    rate = 35 + 45 * np.sin(np.pi * np.clip(t / 0.9, 0, 1)) ** 0.8
    groan = stickslip(n, rate, [(180, 40, 1.0), (420, 70, 0.6), (900, 140, 0.3)], rng, jitter=0.5)
    out = norm(groan) * np.sin(np.pi * np.clip(t / 0.95, 0, 1)) ** 0.7 * (t < 0.95)
    for at in np.sort(rng.uniform(0.35, 1.0, 9)):
        place(out, norm(band(rng.normal(size=int(0.003 * RATE)), 1000, 6000)) * rng.uniform(0.15, 0.45), at)
    place(out, 0.6 * thud(0.3, 55, rng, 0.3), 0.55)
    return out


def latch(rng):
    """A heavy latch dropping home: the clunk, the bolt's snap, a second softer clack."""
    out = np.zeros(int(0.7 * RATE))
    place(out, 1.2 * thud(0.25, 65, rng, 0.6), 0.0)
    place(out, ring(0.3, [(2400, 1.0, 55), (3900, 0.6, 70), (5600, 0.3, 90)], rng, 0.9), 0.025)
    place(out, 0.4 * thud(0.15, 90, rng, 0.5), 0.13)
    place(out, 0.3 * ring(0.2, [(2600, 1.0, 70), (4100, 0.5, 90)], rng, 0.6), 0.14)
    return out


def generate():
    # Loops (no fades: they must meet themselves)
    write("air", air(np.random.default_rng(14001)), 0.45, fade=False)
    write("buzz", buzz(np.random.default_rng(14002)), 0.3, fade=False)
    write("ward", ward(np.random.default_rng(14003)), 0.3, fade=False)
    write("monitor", monitor(np.random.default_rng(14004)), 0.35, fade=False)
    write("torture", torture(np.random.default_rng(14005)), 0.6, fade=False)
    write("contam", contam(np.random.default_rng(14006)), 0.6, fade=False)
    write("dread", dread(np.random.default_rng(14007)), 0.6, fade=False)
    write("heartbeat", heartbeat(np.random.default_rng(14008)), 0.6, fade=False)
    # Far off in the halls
    write("steps1", steps1(np.random.default_rng(14011)), 0.6)
    write("steps2", steps2(np.random.default_rng(14012)), 0.5)
    write("door", door(np.random.default_rng(14013)), 0.55)
    write("whisper1", whisper(np.random.default_rng(14014), 1), 0.45)
    write("whisper2", whisper(np.random.default_rng(14015), 2), 0.45)
    write("gurney", gurney(np.random.default_rng(14016)), 0.5)
    write("beeps", beeps(np.random.default_rng(14017)), 0.45)
    write("chime", chime(np.random.default_rng(14018)), 0.5)
    # The rules
    write("spark", spark(np.random.default_rng(14021)), 0.7)
    write("clatter", clatter(np.random.default_rng(14022)), 0.7)
    write("creak", creak(np.random.default_rng(14023)), 0.7)
    write("latch", latch(np.random.default_rng(14024)), 0.7)
    print(f"Level 14 sounds: {len(WRITTEN)} in {os.path.relpath(OUT, ROOT)} ({', '.join(WRITTEN)})")


if __name__ == "__main__":
    generate()
