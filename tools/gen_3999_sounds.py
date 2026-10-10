"""Level 3999, the Neon Paradise: its sounds, synthesised (3999-plan.md 6.8, less what only the dropped ending needed).
Called from gen_3999.py. Written in quarter-second chunks (libsndfile can crash on long Vorbis writes).

ambient/3999/: four loops of soft mall synthwave (dream, nostalgia, glide, lonely: each wanderer hears one), a quiet
neon hum, the natatorium's lapping, 3999.1's drips and dead relay, Level 10's windmill, Level 11's glitch fizz.
effect/3999/: four 8-bit attract jingles, play, win, lose, taken (a game pulls you in), the walkway belt, the
revolving door, the attendant's chime and three of its wordless syllables. All original.
"""
import os

import numpy as np
import soundfile as sf

from gen_entity_sounds import RATE, band, place, seconds, vowel
from gen_3999_kit import ASSETS, SOUNDS

TAU = 2 * np.pi


def write(folder, name, signal, peak, fade=True):
    path = os.path.join(ASSETS, "sounds", *folder.split("/"), name + ".ogg")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    signal = np.asarray(signal, dtype=np.float64)
    n = min(len(signal) // 4, int(0.006 * RATE))
    if fade and n > 0:
        signal[:n] *= np.linspace(0, 1, n)
        signal[-n:] *= np.linspace(1, 0, n)
    signal = peak * signal / max(1e-9, np.max(np.abs(signal)))
    with sf.SoundFile(path, "w", samplerate=RATE, channels=1, format="OGG", subtype="VORBIS") as f:
        for start in range(0, len(signal), RATE // 4):
            f.write(signal[start:start + RATE // 4].astype(np.float32))
    SOUNDS.append(f"{folder}/{name}")


def hz(semis, root=440.0):
    return root * 2 ** (semis / 12)


def lowpass(x, cutoff, loop=True):
    spectrum = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / RATE)
    spectrum *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(spectrum, n=len(x))


def wrap_add(out, sound, at):
    """Adds a sound into a loop, wrapping what runs past the end round to the start (seamless loops)."""
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


def echo_loop(x, delay, feedback, taps=5):
    out = np.copy(x)
    d = int(delay * RATE)
    for k in range(1, taps + 1):
        out += (feedback ** k) * np.roll(x, d * k)
    return out


def env(n, attack, release):
    e = np.ones(n)
    a, r = int(attack * RATE), int(release * RATE)
    if a > 0:
        e[:min(a, n)] = np.linspace(0, 1, min(a, n))
    if r > 0:
        e[max(0, n - r):] *= np.linspace(1, 0, n - max(0, n - r))
    return e


def saw(f, t, harmonics=10):
    out = np.zeros(len(t))
    for k in range(1, harmonics + 1):
        if f * k > 9000:
            break
        out += np.sin(TAU * f * k * t) / k
    return out


def square(f, t, duty=0.5):
    return np.where((f * t) % 1.0 < duty, 1.0, -1.0)


# ======================================================================== The music

CHORDS = {  # semitones above the key's root
    "maj7": [0, 4, 7, 11], "m7": [0, 3, 7, 10], "maj": [0, 4, 7, 12], "min": [0, 3, 7, 12], "9": [0, 4, 7, 10, 14], "m9": [0, 3, 7, 10, 14],
    "6": [0, 4, 7, 9], "sus": [0, 5, 7, 12],
}


def music(name, root_semis, bpm, progression, bars, mood, seed):
    """Soft mall synthwave: detuned pads, a slow arpeggio with echoes, a round bass, a soft kick and hats, a chorus
    shimmer. progression: [(degree semitones, chord kind)], one chord a bar, repeated. The loop is a whole number of
    bars and every echo and tail wraps round, so it is seamless."""
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    bar = 4 * beat
    total = bars * bar
    n = int(total * RATE)
    pad = np.zeros(n)
    arp = np.zeros(n)
    bass = np.zeros(n)
    drums = np.zeros(n)
    root = hz(root_semis - 12, 440.0)        # the key's root around A3..A4
    for b in range(bars):
        deg, kind = progression[b % len(progression)]
        notes = [deg + s for s in CHORDS[kind]]
        t0 = b * bar
        # Pad: each chord tone two detuned saws, slow attack and release, overlapping the next bar a little
        length = bar * 1.15
        tt = seconds(length)
        e = env(len(tt), mood["attack"], 0.6)
        for s in notes[:4]:
            f = root * 2 ** (s / 12)
            voice = (saw(f * 1.004, tt, 8) + saw(f * 0.996, tt, 8)) * e * 0.18
            voice *= 1 + 0.15 * np.sin(TAU * 0.3 * tt + rng.uniform(0, 6))
            wrap_add(pad, voice, t0)
        # Bass: the root on beats 1 and 3 (2 and 4 a little softer), a round sine with a touch of second harmonic
        for k, amp in ((0, 1.0), (1, 0.55), (2, 0.85), (3, 0.5)):
            if mood.get("sparse") and k % 2:
                continue
            tb = seconds(beat * 0.95)
            fb = root / 2 * 2 ** (deg / 12)
            note = (np.sin(TAU * fb * tb) + 0.25 * np.sin(TAU * 2 * fb * tb)) * np.exp(-tb * 2.2) * env(len(tb), 0.01, 0.08)
            wrap_add(bass, note * amp * 0.5, t0 + k * beat)
        # Arpeggio: chord tones up an octave, in eighths or sixteenths, a soft triangle-ish pluck
        step = beat / mood["arp"]
        count = int(round(bar / step))
        pattern = mood["pattern"]
        for k in range(count):
            if mood.get("sparse") and rng.random() < 0.35:
                continue
            idx = pattern[k % len(pattern)]
            s = notes[idx % len(notes)] + 12 * (1 + idx // len(notes))
            f = root * 2 ** (s / 12)
            ta = seconds(step * 1.8)
            pluck = (np.sin(TAU * f * ta) + 0.3 * np.sin(TAU * 3 * f * ta) / 3 + 0.12 * np.sin(TAU * 2 * f * ta)) * np.exp(-ta * mood["decay"])
            wrap_add(arp, pluck * env(len(ta), 0.004, 0.05) * 0.32, t0 + k * step)
        # Drums: a soft kick on 1 and 3, a closed hat on the off-beats, a snap on 2 and 4 now and then
        if not mood.get("nodrums"):
            for k in range(4):
                if k % 2 == 0:
                    tk = seconds(0.35)
                    kick = np.sin(TAU * np.cumsum(55 + 90 * np.exp(-tk * 30)) / RATE) * np.exp(-tk * 9)
                    wrap_add(drums, kick * 0.9, t0 + k * beat)
                elif mood.get("snap"):
                    ts = seconds(0.18)
                    snap = band(rng.normal(size=len(ts)), 1200, 6000) * np.exp(-ts * 30)
                    wrap_add(drums, snap * 0.18, t0 + k * beat)
                th = seconds(0.06)
                hat = band(rng.normal(size=len(th)), 6000, 14000) * np.exp(-th * 70)
                wrap_add(drums, hat * 0.12, t0 + k * beat + beat / 2)
    pad = lowpass(pad, mood["warmth"])
    # Chorus: a slowly wobbling copy of the pad, mixed in
    shift = (0.012 * RATE * (1 + 0.3 * np.sin(TAU * 0.25 * np.arange(n) / RATE))).astype(int)
    pad = pad + 0.5 * pad[(np.arange(n) - shift) % n]
    arp = echo_loop(arp, beat * 0.75, mood["echo"], 5)
    arp = lowpass(arp, 5200)
    mix_ = 1.0 * pad + 0.9 * arp + 0.8 * bass + 0.55 * drums
    # A faint wash of tape hiss and room, as if from speakers far off in the ceiling
    mix_ += 0.004 * band(rng.normal(size=n), 2000, 9000)
    mix_ = lowpass(mix_, 7000)
    write("ambient/3999", name, mix_, 0.45, fade=False)


def all_music():
    # dreamy: F, 84 bpm, Fmaj7 Em7 Dm7 Cmaj7
    music("music-dream", -4, 84, [(0, "maj7"), (-1, "m7"), (-3, "m7"), (-5, "maj7")], 28,
          dict(attack=1.2, arp=2, pattern=[0, 1, 2, 3, 4, 3, 2, 1], decay=3.2, warmth=2600, echo=0.45, snap=False), 3901)
    # nostalgic: D, 88 bpm, D Bm G A
    music("music-nostalgia", -7, 88, [(0, "maj"), (-3, "min"), (5, "maj"), (7, "sus")], 30,
          dict(attack=0.5, arp=4, pattern=[0, 2, 1, 3, 0, 2, 1, 4], decay=5.5, warmth=3600, echo=0.35, snap=True), 3902)
    # gliding: A dorian, 90 bpm, Am9 D9 Fmaj7 G6
    music("music-glide", 0, 90, [(0, "m9"), (5, "9"), (-4, "maj7"), (-2, "6")], 30,
          dict(attack=0.3, arp=4, pattern=[0, 1, 2, 4, 3, 2, 1, 2], decay=6.5, warmth=4200, echo=0.3, snap=True), 3903)
    # melancholy: C minor, 80 bpm, Cm Ab Eb Bb, sparse, longer echoes, no kick
    music("music-lonely", -9, 80, [(0, "m7"), (-4, "maj7"), (3, "maj7"), (-2, "sus")], 26,
          dict(attack=1.6, arp=2, pattern=[0, 2, 4, 2, 1, 3], decay=2.6, warmth=2200, echo=0.55, sparse=True, nodrums=True), 3904)


# ======================================================================== Ambient loops

def ambients():
    rng = np.random.default_rng(3910)
    # The neon hum: a very quiet 120 Hz buzz with its harmonics, the odd crackle (8 s, whole cycles: seamless)
    t = seconds(8)
    hum = sum(a * np.sin(TAU * f * t) for f, a in ((120, 1.0), (240, 0.35), (360, 0.2), (480, 0.08)))
    hum *= 1 + 0.05 * np.sin(TAU * 0.5 * t)
    crackle = np.zeros(len(t))
    for _ in range(12):
        tc = seconds(rng.uniform(0.005, 0.02))
        wrap_add(crackle, band(rng.normal(size=len(tc)), 2000, 9000) * rng.uniform(0.05, 0.2), rng.uniform(0, 8))
    write("ambient/3999", "neonhum", hum + crackle, 0.12, fade=False)

    # The natatorium: lapping water and a warm echo (20 s)
    n = int(20 * RATE)
    out = np.zeros(n)
    for _ in range(26):
        tl = seconds(rng.uniform(0.3, 0.7))
        slap = band(rng.normal(size=len(tl)), 150, 1600) * np.sin(np.pi * tl / tl[-1]) ** 2
        wrap_add(out, slap * rng.uniform(0.3, 1), rng.uniform(0, 20))
    for _ in range(6):
        td = seconds(0.4)
        f = rng.uniform(700, 1100) * (1 + 1.5 * np.minimum(td, 0.03) / 0.03)
        wrap_add(out, 0.3 * np.sin(TAU * np.cumsum(f) / RATE) * np.exp(-td * 30), rng.uniform(0, 20))
    out = echo_loop(out, 0.11, 0.45, 6) + 0.05 * band(rng.normal(size=n), 100, 900)
    write("ambient/3999", "natatorium", out, 0.4, fade=False)

    # 3999.1: drips, a dead relay ticking somewhere, wind in a vent (30 s)
    n = int(30 * RATE)
    out = np.zeros(n)
    wind = band(rng.normal(size=n), 80, 700) * (0.6 + 0.4 * np.sin(TAU * np.arange(n) / n * 3) ** 2) * 0.25
    out += wind
    for k in range(int(30 / 1.7)):
        tr = seconds(0.03)
        click = band(rng.normal(size=len(tr)), 800, 5000) * np.exp(-tr * 200)
        if rng.random() < 0.8:
            wrap_add(out, click * 0.5, k * 1.7 + rng.uniform(-0.05, 0.05))
    for _ in range(14):
        td = seconds(0.5)
        f = rng.uniform(900, 1500) * (1 + 2.0 * np.minimum(td, 0.025) / 0.025)
        drop = np.sin(TAU * np.cumsum(f) / RATE) * np.exp(-td * 40)
        wrap_add(out, drop * rng.uniform(0.2, 0.5), rng.uniform(0, 30))
    write("ambient/3999", "blackout", echo_loop(out, 0.19, 0.3, 4), 0.45, fade=False)

    # Level 10's windmill: wind over the fields and the creak of the cap and sails (10 s)
    n = int(10 * RATE)
    tt = np.arange(n) / RATE
    gust = 0.7 + 0.3 * np.sin(TAU * tt / 10) ** 2
    out = band(rng.normal(size=n), 100, 1200) * gust * 0.4
    for k in range(5):
        tc = seconds(0.6)
        f = 180 + 60 * np.sin(TAU * 3 * tc)
        creak = vowel(tc, f, [(400, 120, 1.0), (1100, 200, 0.5)], 0.4, rng) * np.sin(np.pi * tc / tc[-1])
        wrap_add(out, creak * 0.5, k * 2 + rng.uniform(0, 0.4))
    write("ambient/3999", "windmill", out, 0.45, fade=False)

    # Level 11's glitch wall: a digital fizz (3 s)
    n = int(3 * RATE)
    out = np.zeros(n)
    block = int(0.02 * RATE)
    for i in range(0, n, block):
        kind = rng.integers(0, 4)
        seg = np.arange(min(block, n - i)) / RATE
        if kind == 0:
            out[i:i + len(seg)] = square(rng.uniform(200, 3000), seg, 0.3) * 0.3
        elif kind == 1:
            out[i:i + len(seg)] = rng.normal(size=len(seg)) * 0.4
        elif kind == 2:
            out[i:i + len(seg)] = np.round(np.sin(TAU * rng.uniform(80, 400) * seg) * 3) / 3 * 0.5
    write("ambient/3999", "glitch", band(out, 150, 9000), 0.4, fade=False)


# ======================================================================== Effects

def chip(notes, step, duty=0.5, decay=6.0, noise_beats=()):
    """An 8-bit tune: square-wave notes (semitones above A4, None for a rest), each `step` seconds."""
    n = int(len(notes) * step * RATE) + int(0.3 * RATE)
    out = np.zeros(n)
    rng = np.random.default_rng(len(notes))
    for k, s in enumerate(notes):
        if s is None:
            continue
        t = seconds(step * 0.95)
        tone = square(hz(s), t, duty) * np.exp(-t * decay) * env(len(t), 0.002, 0.01)
        place(out, tone * 0.5, k * step)
    for k in noise_beats:
        t = seconds(0.08)
        place(out, rng.normal(size=len(t)) * np.exp(-t * 50) * 0.4, k * step)
    return lowpass(out, 9000)


def effects():
    rng = np.random.default_rng(3920)
    # Attract jingles: four little 8-bit fanfares
    tunes = [
        ([3, 7, 10, 15, 10, 15, 19, None, 22], 0.11, 0.5, (0, 4)),
        ([0, 0, 7, 7, 12, 10, 7, None, 5, 7, 12], 0.12, 0.25, (0, 4, 8)),
        ([15, 12, 8, 12, 15, 20, 15, 24, None, 27], 0.1, 0.5, (0, 2, 4, 6)),
        ([-2, 2, 5, 9, 5, 9, 14, 9, 14, 17, None, 21, 21], 0.09, 0.125, (0, 6, 12)),
    ]
    for i, (notes, step, duty, drums) in enumerate(tunes, 1):
        write("effect/3999", f"attract-{i}", chip(notes, step, duty, 5.0, drums), 0.5)
    # Play: bleeps and button clicks, a 5 s loop
    n = int(5 * RATE)
    out = np.zeros(n)
    for k in range(40):
        t = seconds(rng.uniform(0.03, 0.09))
        wrap_add(out, square(hz(rng.integers(0, 30)), t, 0.25) * np.exp(-t * 20) * 0.3, k * 0.125)
    for _ in range(14):
        t = seconds(0.02)
        wrap_add(out, band(rng.normal(size=len(t)), 1500, 6000) * np.exp(-t * 200) * 0.5, rng.uniform(0, 5))
    write("effect/3999", "play", out, 0.45, fade=False)
    # Win: the ratchet of a ticket feed, then a ding
    n = int(1.5 * RATE)
    out = np.zeros(n)
    for k in range(12):
        t = seconds(0.02)
        place(out, band(rng.normal(size=len(t)), 1000, 5000) * np.exp(-t * 180) * 0.6, 0.05 + k * 0.07)
    t = seconds(0.7)
    ding = sum(a * np.sin(TAU * f * t) * np.exp(-t * d) for f, a, d in ((1760, 1.0, 5), (2640, 0.4, 7), (4400, 0.2, 9), (3520, 0.25, 6)))
    place(out, ding * 0.6, 0.85)
    write("effect/3999", "win", out, 0.55)
    # Lose: a descending GAME OVER
    write("effect/3999", "lose", chip([7, 3, 0, -5, -6, -7], 0.17, 0.5, 2.5), 0.5)
    # Taken: a rising whine that fills everything, then a CRT going off
    n = int(3 * RATE)
    t = np.arange(n) / RATE
    f = 200 * (15 ** (np.minimum(t, 2.4) / 2.4)) * (1 + 0.01 * np.sin(TAU * 6 * t))
    whine = np.sin(TAU * np.cumsum(f) / RATE) * np.minimum(1, t / 2.4) ** 2 * (t < 2.45)
    out = whine * 0.5
    tt = seconds(0.5)
    thunk = np.sin(TAU * np.cumsum(70 * np.exp(-tt * 4)) / RATE) * np.exp(-tt * 8) + 0.3 * band(rng.normal(size=len(tt)), 200, 2000) * np.exp(-tt * 30)
    place(out, thunk, 2.45)
    tz = seconds(0.4)
    place(out, 0.15 * np.sin(TAU * np.cumsum(12000 * np.exp(-tz * 6)) / RATE) * np.exp(-tz * 6), 2.45)
    write("effect/3999", "taken", out, 0.6)
    # The walkway: a rubber belt's hum and the tick of its treads (4 s loop)
    n = int(4 * RATE)
    t = np.arange(n) / RATE
    out = 0.3 * np.sin(TAU * 60 * t) + 0.15 * np.sin(TAU * 120 * t) + 0.25 * band(rng.normal(size=n), 60, 500)
    for k in range(16):
        tk = seconds(0.015)
        wrap_add(out, band(rng.normal(size=len(tk)), 1500, 5000) * np.exp(-tk * 250) * 0.4, k * 0.25)
    write("effect/3999", "walkway", out, 0.35, fade=False)
    # The revolving door: a glass swish and the brush of a rubber seal
    n = int(1.5 * RATE)
    t = np.arange(n) / RATE
    noise = rng.normal(size=n)
    sweep = np.zeros(n)
    for i, (lo, hi) in enumerate(((300, 1200), (600, 2400), (1200, 4800), (600, 2400), (300, 1200))):
        seg = slice(int(i * n / 5), int((i + 1) * n / 5))
        sweep[seg] = band(noise, lo, hi)[seg]
    swish = sweep * np.sin(np.pi * t / t[-1]) ** 2
    brush = band(rng.normal(size=n), 150, 900) * np.exp(-((t - 0.9) / 0.12) ** 2) * 0.8
    write("effect/3999", "revolving", swish + brush, 0.5)
    # The attendant's chime: two soft bell tones, high then low, like a cabin chime
    n = int(1.2 * RATE)
    out = np.zeros(n)
    for at, f in ((0.0, 1046.5), (0.38, 784.0)):
        tb = seconds(0.8)
        bell = (np.sin(TAU * f * tb) + 0.3 * np.sin(TAU * 2 * f * tb) * np.exp(-tb * 3) + 0.1 * np.sin(TAU * 3.01 * f * tb)) * np.exp(-tb * 4)
        place(out, bell * env(len(tb), 0.004, 0.05), at)
    write("effect/3999", "chime", out, 0.5)
    # Its voice: soft synthetic syllables, a polite rise and fall, no words
    vowels = [[(700, 90, 1.0), (1200, 120, 0.6), (2600, 200, 0.2)], [(400, 70, 1.0), (2000, 150, 0.5), (2700, 200, 0.25)],
              [(500, 80, 1.0), (900, 100, 0.6), (2400, 200, 0.2)], [(300, 60, 1.0), (2300, 150, 0.4), (3000, 200, 0.2)]]
    for i in range(1, 4):
        r = np.random.default_rng(3930 + i)
        n = int(1.0 * RATE)
        out = np.zeros(n)
        count = 3 + i % 2
        for k in range(count):
            dur = r.uniform(0.14, 0.22)
            ts = seconds(dur)
            p = k / max(1, count - 1)
            f0 = (210 + 40 * np.sin(np.pi * p) - 25 * p) * (1 + 0.04 * np.sin(TAU * 5 * ts))
            f0 = np.round(f0 / 10) * 10          # quantised: synthetic
            syl = vowel(ts, np.full(len(ts), 1.0) * f0, vowels[(k + i) % 4], 0.02, r) * np.maximum(0, np.sin(np.pi * ts / ts[-1])) ** 1.5
            place(out, syl, 0.06 + k * (dur + 0.04))
        out = lowpass(out, 5000)
        write("effect/3999", f"voice-{i}", out, 0.5)


def generate():
    ambients()
    effects()
    all_music()
    print(f"3999 sounds: {len(SOUNDS)}")


if __name__ == "__main__":
    generate()
