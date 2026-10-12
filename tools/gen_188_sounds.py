"""Level 188: every sound (docs/design/new-levels/188-plan.md 4.8), synthesised; mono OGG, written in chunks (libsndfile can
crash on long single Vorbis writes). Called from gen_188.py.

No hum anywhere: the lights here are silent. The courtyard is near silence with a far roof fan; the corridors are
hotel room tone; a downpipe runs into a drain; somebody knocks on glass; the windows whisper; a party goes on
behind one window, heard through it. Loops are seamless: noise is filtered round the loop (the FFT filter is
circular), modulations have a whole number of cycles in the loop, and events that run off the end wrap round.
"""
import math
import os

import numpy as np

from gen_entity_sounds import RATE, band, place, reverb, seconds, thud
from gen_level_sounds import write as write_ogg

ROOT = os.path.join(os.path.dirname(__file__), "..")
SOUNDS = os.path.join(ROOT, "assets", "backrooms", "sounds")

PLAN = {"ambient/188": ["courtyard", "corridor", "pipe"],
        "effect/188": ["knock", "whisper", "blindup", "blinddown", "grab", "recoil", "taken", "hatch", "partymuffled",
                       "liftchime", "tvwall", "vacuum", "icedrop", "thump"]}
WRITTEN = []


def write(folder, name, signal, peak, fade=True):
    write_ogg(folder, name, signal, peak, fade)
    WRITTEN.append(f"{folder}/{name}")


def norm(x):
    return x / max(1e-9, np.max(np.abs(x)))


def wrap_place(out, sound, at):
    """Places a sound in a loop, the part that runs off the end wrapping round to the start."""
    i = int(at * RATE) % len(out)
    n = len(sound)
    first = min(n, len(out) - i)
    out[i:i + first] += sound[:first]
    if n > first:
        out[:n - first] += sound[first:]


def lowpass(x, hi):
    return band(x, 0, hi)


def chime(f, length, rng=None, partials=((1, 1.0), (2.76, 0.4), (5.4, 0.18), (8.9, 0.08))):
    t = seconds(length)
    out = np.zeros(len(t))
    for k, a in partials:
        out += a * np.sin(2 * np.pi * f * k * t) * np.exp(-t * (2.5 + 2.2 * k))
    return out


def courtyard(rng):
    t = seconds(45)
    air = norm(band(rng.normal(size=len(t)), 40, 260))
    breath = 0.75 + 0.25 * np.sin(2 * np.pi * t * 2 / 45 + 0.4) + 0.1 * np.sin(2 * np.pi * t * 5 / 45 + 1.7)
    hiss = norm(band(rng.normal(size=len(t)), 1800, 5200))
    # the far roof fan: a low drone pulsing at its blade rate (99 beats in the loop), 30 dB down
    fan = np.sin(2 * np.pi * 47 * t) + 0.5 * np.sin(2 * np.pi * 94 * t)
    fan *= 0.6 + 0.4 * np.sin(2 * np.pi * (99 / 45) * t) ** 2
    out = 0.8 * air * breath + 0.05 * hiss * breath + 0.032 * fan
    write("ambient/188", "courtyard", out, 0.22, fade=False)


def corridor(rng):
    t = seconds(45)
    wash = norm(band(rng.normal(size=len(t)), 90, 4200))
    low = norm(band(rng.normal(size=len(t)), 40, 180))
    plant = np.sin(2 * np.pi * 120 * t) + 0.3 * np.sin(2 * np.pi * 240 * t)
    sway = 0.85 + 0.15 * np.sin(2 * np.pi * t * 3 / 45)
    out = 0.35 * wash * sway + 0.5 * low + 0.025 * plant
    write("ambient/188", "corridor", out, 0.25, fade=False)


def pipe(rng):
    n = 8 * RATE
    t = seconds(8)
    stream = norm(band(rng.normal(size=n), 700, 5200))
    flutter = norm(band(rng.normal(size=n), 2, 18))  # circular too: the stream's unsteadiness loops
    out = 0.35 * stream * (0.65 + 0.35 * flutter)
    for k in range(26):  # gurgles: little rising bubbles
        L = rng.uniform(0.03, 0.09)
        tt = seconds(L)
        f0 = rng.uniform(260, 700)
        b = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 1.6 * tt / L)) / RATE) * np.sin(np.pi * tt / L) ** 2
        wrap_place(out, 0.5 * b, rng.uniform(0, 8))
    for k in range(9):  # drips into the puddle
        tt = seconds(0.25)
        f = 1100 * (1 + 2 * np.minimum(tt, 0.02) / 0.02)
        d = np.sin(2 * np.pi * np.cumsum(f) / RATE) * np.exp(-tt * 40)
        wrap_place(out, 0.6 * d, rng.uniform(0, 8))
    write("ambient/188", "pipe", out, 0.5, fade=False)


def knock(rng):
    out = np.zeros(int(1.5 * RATE))
    for k, at in enumerate((0.05, 0.30, 0.55)):
        rap = thud(0.12, 160 + 10 * k, rng, 0.25)
        tt = seconds(0.25)
        ring = (np.sin(2 * np.pi * 2350 * tt) + 0.6 * np.sin(2 * np.pi * 3900 * tt)) * np.exp(-tt * 30)
        place(out, 0.8 * rap, at)
        place(out, 0.18 * ring * (0.9 - 0.15 * k), at)
    write("effect/188", "knock", reverb(out, 0.3), 0.5)


def whisper(rng):
    """Overlapping soft, warm, wordless whispers: noise through vowel formants in syllables, three voices, slow."""
    n = 10 * RATE
    out = np.zeros(n)
    vowels = [((600, 160, 1.0), (1100, 200, 0.7), (2500, 300, 0.3)), ((400, 120, 1.0), (1900, 260, 0.6), (2700, 300, 0.3)),
              ((500, 140, 1.0), (850, 150, 0.7), (2400, 300, 0.25)), ((300, 100, 1.0), (2200, 300, 0.5), (3000, 300, 0.25)),
              ((700, 180, 0.9), (1300, 220, 0.6), (2600, 300, 0.3))]
    for voice in range(3):
        at = rng.uniform(0, 1.0)
        while at < 10:
            L = rng.uniform(0.18, 0.5)
            m = int(L * RATE)
            noise = rng.normal(size=m)
            spec = np.fft.rfft(noise)
            f = np.fft.rfftfreq(m, 1 / RATE)
            shape = sum(a * np.exp(-((f - fc) / bw) ** 2) for fc, bw, a in vowels[rng.integers(len(vowels))])
            shape += 0.12 * np.exp(-((f - 6000) / 2000) ** 2)  # a little sibilance
            syl = np.fft.irfft(spec * shape, n=m)
            env = np.sin(np.pi * np.arange(m) / m) ** 1.5
            wrap_place(out, norm(syl) * env * rng.uniform(0.4, 1.0), at)
            at += L + rng.uniform(0.05, 0.6 if rng.random() < 0.8 else 1.6)
    slow = 0.7 + 0.3 * np.sin(2 * np.pi * seconds(10) / 10 * 2)
    write("effect/188", "whisper", out * slow, 0.35, fade=False)


def blind(rng, up):
    L = 1.0
    out = np.zeros(int(L * RATE))
    # the roller's ratchet: clicks, speeding up (going up) or steady (coming down)
    at, k = 0.04, 0
    end = 0.78 if up else 0.85
    while at < end:
        tt = seconds(0.012)
        click = band(rng.normal(size=len(tt)), 2500, 9000) * np.exp(-tt * 500)
        place(out, 0.25 * click, at)
        gap = (0.045 - 0.03 * (at / end)) if up else 0.05 + 0.01 * math.sin(k)
        at += gap * rng.uniform(0.85, 1.15)
        k += 1
    swish = norm(band(rng.normal(size=len(out)), 600, 4000)) * np.clip(np.sin(np.pi * np.arange(len(out)) / (end * RATE)), 0, 1) * 0.12
    out += swish
    # the snap at the top (or the bar settling at the bottom)
    place(out, 0.9 * thud(0.08, 420 if up else 220, rng, 0.8 if up else 0.3), end)
    write("effect/188", "blindup" if up else "blinddown", reverb(out, 0.15), 0.55)


def grab(rng):
    L = 0.8
    t = seconds(L)
    sweep = 200 + 1300 * np.minimum(1, t / 0.35)
    lunge = norm(band(rng.normal(size=len(t)), 150, 2000)) * np.sin(np.pi * np.clip(t / 0.45, 0, 1)) ** 2
    lunge *= 0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(sweep) / RATE / 40)
    out = 0.6 * lunge
    for k in range(5):  # wet sinews: soft squelches
        m = int(0.05 * RATE)
        sq = band(rng.normal(size=m), 300, 1400) * np.hanning(m)
        place(out, 0.5 * sq, 0.12 + 0.06 * k + rng.uniform(0, 0.02))
    at = 0.42
    while at < 0.75:  # the glass creaking under the strain
        tt = seconds(0.008)
        place(out, 0.25 * np.sin(2 * np.pi * rng.uniform(420, 700) * tt) * np.exp(-tt * 300), at)
        at += rng.uniform(0.006, 0.02)
    write("effect/188", "grab", reverb(out, 0.2), 0.75)


def recoil(rng):
    t = seconds(0.6)
    hiss = norm(band(rng.normal(size=len(t)), 2000, 8000)) * np.exp(-t * 6) * np.minimum(1, t / 0.02)
    out = 0.5 * hiss
    place(out, 0.9 * thud(0.12, 140, rng, 0.9), 0.32)
    place(out, 0.3 * band(rng.normal(size=int(0.02 * RATE)), 3000, 9000), 0.32)
    write("effect/188", "recoil", reverb(out, 0.15), 0.7)


def taken(rng):
    t = seconds(2.0)
    rush = norm(band(rng.normal(size=len(t)), 200, 3000)) * np.clip(t / 1.0, 0, 1) ** 2 * np.clip((1.25 - t) / 0.1, 0, 1)
    out = 0.6 * rush
    place(out, lowpass(thud(0.4, 60, rng, 0.1), 400), 1.2)
    c = chime(1320, 0.7)
    place(out, 0.25 * lowpass(c, 3000), 1.35)
    write("effect/188", "taken", reverb(out, 0.4), 0.7)


def hatch(rng):
    L = 1.2
    out = np.zeros(int(L * RATE))
    at = 0.02
    while at < 0.95:  # the hinge squealing in stick-slip bursts, pitch wandering
        f = 520 + 260 * math.sin(at * 7) + rng.uniform(-40, 40)
        tt = seconds(0.03)
        place(out, 0.35 * np.sin(2 * np.pi * f * tt) * np.sin(np.pi * tt / 0.03), at)
        at += rng.uniform(0.012, 0.03)
    scrape = norm(band(rng.normal(size=len(out)), 300, 2500)) * np.clip(np.arange(len(out)) / (0.95 * RATE), 0, 1) * (np.arange(len(out)) < 0.95 * RATE)
    out += 0.25 * scrape
    place(out, 1.0 * thud(0.25, 90, rng, 0.6), 0.96)
    place(out, 0.3 * chime(310, 0.25, partials=((1, 1), (2.3, 0.6), (4.1, 0.3))), 0.96)
    write("effect/188", "hatch", reverb(out, 0.3), 0.85)


def partymuffled(rng):
    """A party heard through glass: a tinny little tune (original), a beat, cheers; low-passed hard. A 14 s loop: the
    tune is 14 bars of 1 s."""
    n = 14 * RATE
    out = np.zeros(n)
    # an original eight-bar tune on a cheap square lead, then six bars of it again a little varied
    notes = [72, 74, 76, 79, 76, 74, 72, 67, 69, 72, 74, 72, 69, 67, 64, 67,
             72, 74, 76, 79, 81, 79, 76, 74, 72, 76, 74, 72]
    step = 0.5
    for i, nnum in enumerate(notes):
        f = 440 * 2 ** ((nnum - 69) / 12)
        tt = seconds(step * 0.9)
        sq = np.sign(np.sin(2 * np.pi * f * tt)) * np.exp(-tt * 3) * np.minimum(1, tt / 0.01)
        wrap_place(out, 0.25 * sq, i * step)
    for b in range(28):  # a thumping beat, two to the bar
        wrap_place(out, 0.6 * thud(0.15, 55, rng, 0.05), b * 0.5)
    for k in range(3):  # cheers, and someone laughing
        L = rng.uniform(0.6, 1.2)
        m = int(L * RATE)
        cheer = band(rng.normal(size=m), 300, 1800) * np.sin(np.pi * np.arange(m) / m) ** 2
        wrap_place(out, 0.4 * norm(cheer), rng.uniform(0, 14))
    out = lowpass(out, 650)
    write("effect/188", "partymuffled", out, 0.45, fade=False)


def liftchime(rng):
    out = np.zeros(int(1.0 * RATE))
    place(out, chime(880, 0.8), 0.02)
    place(out, chime(698, 0.8), 0.32)
    write("effect/188", "liftchime", reverb(lowpass(out, 2500), 0.5), 0.5)


def tvwall(rng):
    from gen_entity_sounds import vowel
    n = 6 * RATE
    out = np.zeros(n)
    vowels = [((700, 120, 1), (1200, 150, 0.6)), ((400, 100, 1), (2000, 200, 0.5)), ((500, 100, 1), (900, 120, 0.6)), ((300, 80, 1), (2300, 250, 0.4))]
    for voice, base in enumerate((110, 190)):
        at = 0.1 + voice * 0.4
        while at < 5.6:
            L = rng.uniform(0.08, 0.22)
            tt = seconds(L)
            f0 = np.full(len(tt), base * rng.uniform(0.9, 1.15)) * (1 + 0.08 * np.sin(2 * np.pi * 3 * tt))
            syl = vowel(tt, f0, vowels[rng.integers(len(vowels))], 0.1, rng) * np.sin(np.pi * tt / L)
            place(out, 0.5 * norm(syl), at)
            at += L + rng.uniform(0.02, 0.25 if rng.random() < 0.8 else 0.9)
    static = norm(band(rng.normal(size=n), 1500, 5000)) * 0.08
    music = sum(np.sin(2 * np.pi * f * seconds(6)) for f in (220, 277, 330)) * 0.05
    out = lowpass(out + static + music, 900)
    write("effect/188", "tvwall", reverb(out, 0.3), 0.4)


def vacuum(rng):
    t = seconds(8)
    spin = np.clip(t / 1.0, 0, 1) * np.clip((7.2 - t) / 1.2, 0, 1)
    f = 90 + 110 * spin
    motor = np.sign(np.sin(2 * np.pi * np.cumsum(f) / RATE)) * 0.3 + np.sin(2 * np.pi * np.cumsum(2 * f) / RATE) * 0.4
    air = norm(band(rng.normal(size=len(t)), 500, 3200))
    out = (motor * 0.5 + air * 0.6) * spin * (0.85 + 0.15 * np.sin(2 * np.pi * t * 0.7))
    out = lowpass(out, 1800)
    write("effect/188", "vacuum", reverb(out, 0.5), 0.4)


def icedrop(rng):
    out = np.zeros(int(1.5 * RATE))
    at = 0.03
    for k in range(14):
        tt = seconds(0.06)
        f = rng.uniform(2200, 4800)
        clink = (np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 1.7 * tt)) * np.exp(-tt * 70)
        place(out, (0.9 - 0.05 * k) * clink, at)
        place(out, 0.3 * thud(0.05, rng.uniform(300, 600), rng, 0.6), at)
        at += rng.uniform(0.02, 0.09) * (1 + k * 0.08)
    write("effect/188", "icedrop", reverb(out, 0.25), 0.5)


def thump(rng):
    out = np.zeros(int(1.0 * RATE))
    for k, at in enumerate((0.04, 0.37, 0.70)):
        place(out, lowpass(thud(0.25, 58 - 3 * k, rng, 0.1), 300) * (1 - 0.1 * k), at)
    write("effect/188", "thump", reverb(out, 0.4), 0.6)


def generate():
    rng = np.random.default_rng(188)
    courtyard(rng)
    corridor(rng)
    pipe(rng)
    knock(rng)
    whisper(rng)
    blind(rng, True)
    blind(rng, False)
    grab(rng)
    recoil(rng)
    taken(rng)
    hatch(rng)
    partymuffled(rng)
    liftchime(rng)
    tvwall(rng)
    vacuum(rng)
    icedrop(rng)
    thump(rng)
    return existing()


def existing():
    written, missing = [], []
    for folder, names in PLAN.items():
        for nm in names:
            (written if os.path.exists(os.path.join(SOUNDS, *folder.split("/"), nm + ".ogg")) else missing).append(f"{folder}/{nm}")
    return {"written": written, "missing": missing}


if __name__ == "__main__":
    print(generate())
