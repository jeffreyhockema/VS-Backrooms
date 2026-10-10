"""The Hub's sounds (for tools/gen_hub.py), synthesised like gen_level_sounds.py and written a little at a time.

ambient/hub: silence (the near-silent drone of the tunnels, a seamless 60 s loop; the code steps its pitch every few
minutes), wind (round the Tower, a 30 s loop), thunder1-3 (far off, through thick walls).
effect/hub: keychime (a struck Level Key, 500 Hz), keyturn (three turns of the key), doorgrind (a concrete slab grinding
aside), keyjingle (the Keymaster's ring of keys), manifest (a door that wasn't there), keymaster (a displeased "hm").
"""
import numpy as np

from gen_entity_sounds import RATE, band, place, seconds, vowel
from gen_level_sounds import write


def periodic_noise(n, rng, shape):
    """Noise that loops seamlessly (built in the frequency domain), its spectrum shaped by shape(f)."""
    spectrum = rng.normal(size=n // 2 + 1) + 1j * rng.normal(size=n // 2 + 1)
    f = np.fft.rfftfreq(n, 1 / RATE)
    spectrum *= shape(f)
    spectrum[0] = 0
    return np.fft.irfft(spectrum, n=n)


def lowpass(x, cutoff):
    return band(x, 0, cutoff)


def silence():
    """Almost nothing: a 45 Hz hum with a little of its octave, swelling once every 10 s, and the faintest air."""
    rng = np.random.default_rng(1701)
    n = int(60 * RATE)
    t = np.arange(n) / RATE
    hum = np.sin(2 * np.pi * 45 * t) + 0.35 * np.sin(2 * np.pi * 90 * t + 0.7) + 0.08 * np.sin(2 * np.pi * 135 * t)
    hum *= 0.75 + 0.25 * np.sin(2 * np.pi * 0.1 * t)
    air = periodic_noise(n, rng, lambda f: np.exp(-((f - 180) / 140) ** 2))
    air *= 0.25 / max(1e-9, np.max(np.abs(air)))
    write("ambient/hub", "silence", hum / 1.4 + air, 0.12, fade=False)


def wind():
    """Wind round stone, low and gusting: two slow swells in whole cycles of the loop."""
    rng = np.random.default_rng(1702)
    n = int(30 * RATE)
    t = np.arange(n) / RATE
    base = periodic_noise(n, rng, lambda f: np.exp(-((f - 260) / 220) ** 2) + 0.3 * np.exp(-((f - 700) / 300) ** 2))
    base /= np.max(np.abs(base))
    gust = 0.45 + 0.3 * np.sin(2 * np.pi * t / 7.5) ** 2 + 0.25 * np.sin(2 * np.pi * t / 10 + 1.3) ** 4
    # A whistle round an edge now and then: a narrow band, swelling with the gusts
    whistle = periodic_noise(n, rng, lambda f: np.exp(-((f - 1150) / 25) ** 2))
    whistle /= np.max(np.abs(whistle))
    out = base * gust + 0.12 * whistle * np.sin(2 * np.pi * t / 15) ** 6
    write("ambient/hub", "wind", out, 0.4, fade=False)


def thunder(k):
    """Thunder a long way off, heard through thick stone: a crack gone dull, then a long rolling rumble."""
    rng = np.random.default_rng(1710 + k)
    length = (4.2, 5.4, 6.0)[k - 1]
    n = int(length * RATE)
    t = np.arange(n) / RATE
    out = np.zeros(n)
    rumble = lowpass(rng.normal(size=n), 160)
    env = np.minimum(1, t / 0.25) * np.exp(-t / (length * 0.35))
    # Rolling: a few swells as the sound comes back off far clouds
    for j in range(rng.integers(3, 6)):
        at = rng.uniform(0.2, length * 0.6)
        env += 0.6 * np.exp(-((t - at) / rng.uniform(0.3, 0.7)) ** 2)
    out += rumble * env
    crack = lowpass(rng.normal(size=int(0.4 * RATE)), 400) * np.exp(-seconds(0.4) * 9)
    place(out, 0.8 * crack, 0.05)
    write("ambient/hub", f"thunder{k}", lowpass(out, 220), 0.6)


def keychime():
    """A struck Level Key: 500 Hz exactly, with a tuning fork's inharmonic partials, a fast attack, a 1.4 s decay."""
    t = seconds(1.6)
    out = (np.sin(2 * np.pi * 500 * t) * np.exp(-t / 0.55)
           + 0.35 * np.sin(2 * np.pi * 500 * 2.76 * t) * np.exp(-t / 0.18)
           + 0.15 * np.sin(2 * np.pi * 500 * 5.4 * t) * np.exp(-t / 0.07))
    out *= np.minimum(1, t / 0.002)
    tick = band(np.random.default_rng(1720).normal(size=len(t)), 3000, 9000) * np.exp(-t * 400) * 0.3
    write("effect/hub", "keychime", out + tick, 0.6)


def keyturn():
    """Three heavy turns of a key in a lock: each a slide of metal on metal, then a ratchet's clack."""
    rng = np.random.default_rng(1721)
    n = int(1.2 * RATE)
    out = np.zeros(n)
    for k in range(3):
        at = 0.05 + k * 0.36
        slide = band(rng.normal(size=int(0.22 * RATE)), 1500, 6000)
        ts = seconds(0.22)
        place(out, 0.18 * slide * np.sin(np.pi * ts / 0.22), at)
        tc = seconds(0.12)
        clack = (band(rng.normal(size=len(tc)), 800, 5000) * np.exp(-tc * 120)
                 + 0.8 * np.sin(2 * np.pi * 1900 * tc) * np.exp(-tc * 60) + 0.5 * np.sin(2 * np.pi * 320 * tc) * np.exp(-tc * 40))
        place(out, clack, at + 0.22)
    write("effect/hub", "keyturn", out, 0.65)


def doorgrind():
    """A great concrete slab grinding aside: a low, rough scrape that judders, then the thud as it stops."""
    rng = np.random.default_rng(1722)
    n = int(2.2 * RATE)
    t = np.arange(n) / RATE
    scrape = band(rng.normal(size=n), 60, 900)
    judder = 0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 7.3 * t + 2 * np.sin(2 * np.pi * 1.1 * t)))
    env = np.minimum(1, t / 0.2) * np.clip((1.85 - t) / 0.3, 0, 1)
    grit = band(rng.normal(size=n), 1500, 5000) * (rng.random(n) < 0.004) * 2
    out = scrape * judder * env + grit * env
    tt = seconds(0.5)
    thud = np.sin(2 * np.pi * 55 * tt * (1 - 0.3 * tt)) * np.exp(-tt * 9) + 0.4 * band(rng.normal(size=len(tt)), 60, 400) * np.exp(-tt * 20)
    place(out, 2.2 * thud, 1.72)
    write("effect/hub", "doorgrind", out, 0.7)


def keyjingle():
    """A big iron ring of keys, shaken: many small bright strikes, each its own ring."""
    rng = np.random.default_rng(1723)
    n = int(1.0 * RATE)
    out = np.zeros(n)
    for k in range(34):
        at = rng.uniform(0, 0.75) * (1 if k % 3 else 0.5)
        tk = seconds(rng.uniform(0.08, 0.25))
        f = rng.uniform(2400, 6500)
        strike = (np.sin(2 * np.pi * f * tk) + 0.5 * np.sin(2 * np.pi * f * 1.52 * tk)) * np.exp(-tk * rng.uniform(25, 60))
        strike += band(rng.normal(size=len(tk)), 4000, 10000) * np.exp(-tk * 300) * 0.4
        place(out, strike * rng.uniform(0.3, 1), at)
    write("effect/hub", "keyjingle", out, 0.55)


def manifest():
    """A deep pressure thump, felt more than heard, and then almost nothing: a door that was not there, is."""
    rng = np.random.default_rng(1724)
    n = int(1.5 * RATE)
    t = np.arange(n) / RATE
    boom = np.sin(2 * np.pi * np.cumsum(38 - 14 * np.minimum(1, t / 0.6)) / RATE) * np.minimum(1, t / 0.01) * np.exp(-t * 3.2)
    air = lowpass(rng.normal(size=n), 120) * np.exp(-t * 6) * 0.4
    tail = band(rng.normal(size=n), 200, 800) * np.exp(-((t - 0.9) / 0.25) ** 2) * 0.03
    write("effect/hub", "manifest", boom + air + tail, 0.75)


def keymaster():
    """A low, displeased 'hm', through the nose, falling."""
    rng = np.random.default_rng(1725)
    t = seconds(0.8)
    f0 = 92 * (1.08 - 0.18 * t / 0.8)
    hum = vowel(t, f0, ((260, 70, 1.0), (1000, 200, 0.12), (2300, 300, 0.05)), 0.04, rng)
    env = np.minimum(1, t / 0.05) * np.minimum(1, (0.8 - t) / 0.25) ** 1.5
    breath = band(rng.normal(size=len(t)), 300, 2500) * np.exp(-((t - 0.02) / 0.04) ** 2) * 0.15
    write("effect/hub", "keymaster", lowpass(hum * env, 3000) + breath, 0.6)


def generate():
    silence()
    wind()
    for k in (1, 2, 3):
        thunder(k)
    keychime()
    keyturn()
    doorgrind()
    keyjingle()
    manifest()
    keymaster()
