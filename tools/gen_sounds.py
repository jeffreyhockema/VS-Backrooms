"""Synthesises the fluorescent hum-buzz loop and the crackle of failing lights.

Real magnetic ballasts buzz at 120 Hz (twice the 60 Hz mains frequency) with strong harmonics. Every component
completes a whole number of cycles in the loop length, so the loop is seamless.

Run from the repo root:  python tools/gen_sounds.py
"""
import os

import numpy as np
import soundfile as sf


def _write_in_chunks(path, data, rate, format="OGG", subtype="VORBIS"):
    """libsndfile can crash when asked to encode a long Vorbis buffer in one call, so feed it a little at a time."""
    with sf.SoundFile(path, "w", samplerate=rate, channels=1, format=format, subtype=subtype) as f:
        for start in range(0, len(data), rate // 4):
            f.write(data[start:start + rate // 4])


sf.write = _write_in_chunks

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "assets", "backrooms", "sounds", "ambient", "hum.ogg")

RATE = 44100
SECONDS = 6
t = np.arange(RATE * SECONDS) / RATE
rng = np.random.default_rng(7)

signal = np.zeros_like(t)
# Ballast buzz: 120 Hz and its harmonics, with odd harmonics a little stronger for that rough edge
for n, amp in [(1, 1.0), (2, 0.55), (3, 0.5), (4, 0.25), (5, 0.3), (6, 0.12), (7, 0.15), (9, 0.08), (11, 0.05)]:
    signal += amp * np.sin(2 * np.pi * 120 * n * t + rng.uniform(0, 2 * np.pi))
# Mains undertone
signal += 0.25 * np.sin(2 * np.pi * 60 * t)

# Slow, uneasy wavering (whole cycles per loop)
signal *= 1 + 0.12 * np.sin(2 * np.pi * (1 / 3) * t) + 0.06 * np.sin(2 * np.pi * (1 / 2) * t + 1.3)

# Soft saturation gives the buzz its grit
signal = np.tanh(1.6 * signal / np.max(np.abs(signal)))

# Faint electrical hiss, generated in the frequency domain so it loops seamlessly
spectrum = rng.normal(size=len(t) // 2 + 1) + 1j * rng.normal(size=len(t) // 2 + 1)
freqs = np.fft.rfftfreq(len(t), 1 / RATE)
spectrum *= (freqs > 2000) * (freqs < 9000)
hiss = np.fft.irfft(spectrum, n=len(t))
signal += 0.04 * hiss / np.max(np.abs(hiss))

# Kept quiet: it plays constantly, scaled up by the number of nearby lights
signal = 0.12 * signal / np.max(np.abs(signal))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
sf.write(OUT, signal.astype(np.float32), RATE, format="OGG", subtype="VORBIS")
print("wrote", os.path.relpath(OUT, ROOT))


# Failing-light crackles: a ballast "tink" plus a burst of arcing buzz, three variants
for variant in range(1, 4):
    rng = np.random.default_rng(100 + variant)
    length = rng.uniform(0.15, 0.35)
    n = int(RATE * length)
    tt = np.arange(n) / RATE
    buzz = np.zeros(n)
    for h, amp in [(1, 1.0), (2, 0.6), (3, 0.7), (5, 0.4), (7, 0.25)]:
        buzz += amp * np.sign(np.sin(2 * np.pi * 120 * h * tt + rng.uniform(0, 6)))
    # Arcing: the buzz cuts in and out
    gate = (rng.random(n // 220 + 1) < 0.6).repeat(220)[:n]
    crackle = rng.normal(size=n) * (rng.random(n) < 0.02) * 3
    tink = np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 60)
    envelope = np.minimum(1, tt * 200) * np.exp(-tt * rng.uniform(6, 12))
    out = (0.5 * buzz * gate + crackle + 0.8 * tink) * envelope
    out = 0.5 * out / np.max(np.abs(out))
    path = os.path.join(ROOT, "assets", "backrooms", "sounds", "effect", f"flicker{variant}.ogg")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sf.write(path, out.astype(np.float32), RATE, format="OGG", subtype="VORBIS")
    print("wrote", os.path.relpath(path, ROOT))

# Steam leak hiss: a steady jet of band-limited noise, built in the frequency domain so it loops seamlessly
rng = np.random.default_rng(55)
n = RATE * 4
spectrum = rng.normal(size=n // 2 + 1) + 1j * rng.normal(size=n // 2 + 1)
freqs = np.fft.rfftfreq(n, 1 / RATE)
spectrum *= np.exp(-((freqs - 4500) / 2500) ** 2) + 0.3 * np.exp(-((freqs - 9000) / 3000) ** 2)
hiss = np.fft.irfft(spectrum, n=n)
tt = np.arange(n) / RATE
hiss = 0.25 * hiss / np.max(np.abs(hiss))
path = os.path.join(ROOT, "assets", "backrooms", "sounds", "ambient", "steam.ogg")
sf.write(path, hiss.astype(np.float32), RATE, format="OGG", subtype="VORBIS")
print("wrote", os.path.relpath(path, ROOT))


def loop_noise(n, rng, shape):
    """Noise of a given spectral shape that loops seamlessly."""
    spectrum = rng.normal(size=n // 2 + 1) + 1j * rng.normal(size=n // 2 + 1)
    spectrum *= shape(np.fft.rfftfreq(n, 1 / RATE))
    out = np.fft.irfft(spectrum, n=n)
    return out / np.max(np.abs(out))


def save_ogg(name, signal, peak):
    path = os.path.join(ROOT, "assets", "backrooms", "sounds", "ambient", name + ".ogg")
    signal = peak * signal / np.max(np.abs(signal))
    sf.write(path, signal.astype(np.float32), RATE, format="OGG", subtype="VORBIS")
    print("wrote", os.path.relpath(path, ROOT))


# Transformer: a deep 60 Hz hum with harmonics and the odd electrical crackle
rng = np.random.default_rng(71)
n = RATE * 6
tt = np.arange(n) / RATE
hum = sum(a * np.sin(2 * np.pi * 60 * k * tt + rng.uniform(0, 6)) for k, a in ((1, 1.0), (2, 0.8), (3, 0.35), (4, 0.3), (6, 0.15)))
crackle = rng.normal(size=n) * (rng.random(n) < 0.0015) * 4
save_ogg("transformer", np.tanh(1.3 * hum / np.max(np.abs(hum))) + 0.3 * crackle, 0.2)

# Rain on the windows: a soft wash of noise with drops tapping the glass
rng = np.random.default_rng(72)
n = RATE * 8
wash = loop_noise(n, rng, lambda f: np.exp(-((f - 1800) / 2600) ** 2) + 0.4 * np.exp(-((f - 6000) / 3000) ** 2))
drops = np.zeros(n)
for start in rng.integers(0, n - 2000, 900):
    length = int(rng.integers(200, 900))
    drops[start:start + length] += rng.normal(size=length) * np.exp(-np.arange(length) / (length / 6)) * rng.uniform(0.3, 1)
save_ogg("rain", 0.8 * wash + 0.5 * drops / np.max(np.abs(drops)), 0.3)

# Jazz: a lo-fi swing loop drifting from another room (ii-V-I in F, walking bass, piano, brushes, record crackle)
rng = np.random.default_rng(73)
bpm, bars = 116, 8
beat = 60 / bpm
n = int(RATE * beat * 4 * bars)
tt = np.arange(n) / RATE
jazz = np.zeros(n)


def note(freq, start, length, amp, harmonics=((1, 1.0), (2, 0.4), (3, 0.15))):
    i0, i1 = int(start * RATE), min(n, int((start + length) * RATE))
    local = np.arange(i1 - i0) / RATE
    tone = sum(a * np.sin(2 * np.pi * freq * k * local) for k, a in harmonics)
    jazz[i0:i1] += amp * tone * np.exp(-local * 3.0) * np.minimum(1, local * 200)


midi = lambda m: 440 * 2 ** ((m - 69) / 12)
chords = [(55, 58, 62, 65), (48, 52, 55, 58), (53, 57, 60, 64), (53, 57, 60, 64)]  # Gm7, C7, Fmaj7, Fmaj7
bass_lines = [(43, 46, 50, 48), (36, 40, 43, 46), (41, 45, 48, 45), (41, 43, 45, 46)]
for bar in range(bars):
    chord, bass = chords[bar % 4], bass_lines[bar % 4]
    for b in range(4):
        t0 = (bar * 4 + b) * beat
        note(midi(bass[b]), t0, beat * 0.95, 0.5, ((1, 1.0), (2, 0.5)))
        if b in (1, 3):  # comping on 2 and 4, swung
            for m in chord:
                note(midi(m + 12), t0 + beat * 0.08, beat * 0.6, 0.12)
        # Brushes: swung ride pattern of soft noise taps
        for offset in (0, beat * 0.66) if b % 2 else (0,):
            i0 = int((t0 + offset) * RATE)
            length = int(0.08 * RATE)
            if i0 + length < n:
                jazz[i0:i0 + length] += rng.normal(size=length) * np.exp(-np.arange(length) / (length / 5)) * 0.08

# Old record: muffle the highs, add crackle
spectrum = np.fft.rfft(jazz)
spectrum *= np.exp(-(np.fft.rfftfreq(n, 1 / RATE) / 2200) ** 2)
jazz = np.fft.irfft(spectrum, n=n)
crackle = rng.normal(size=n) * (rng.random(n) < 0.002) * 0.6
save_ogg("jazz", jazz / np.max(np.abs(jazz)) + 0.15 * crackle, 0.3)


# Power-down: the hum of a whole floor of lights sagging in pitch and dying, as a Reality Shift begins
length = 3.5
n = int(RATE * length)
tt = np.arange(n) / RATE
pitch = 120 * (1 - 0.75 * (tt / length) ** 1.5)
phase = 2 * np.pi * np.cumsum(pitch) / RATE
whine = sum(a * np.sin(k * phase) for k, a in ((1, 1.0), (2, 0.5), (3, 0.45), (5, 0.2)))
whine *= np.minimum(1, tt * 8) * (1 - tt / length) ** 0.7
rng = np.random.default_rng(81)
clicks = rng.normal(size=n) * (rng.random(n) < 0.004) * np.exp(-tt * 1.5) * 2
path = os.path.join(ROOT, "assets", "backrooms", "sounds", "effect", "powerdown.ogg")
out = np.tanh(1.4 * whine / np.max(np.abs(whine))) + clicks
sf.write(path, (0.6 * out / np.max(np.abs(out))).astype(np.float32), RATE, format="OGG", subtype="VORBIS")
print("wrote", os.path.relpath(path, ROOT))
