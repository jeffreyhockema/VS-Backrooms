"""The working props (src/Props/): what is new for them, as assets.

Fire alarms, steam valves, breakers and car alarms are old blocks given behaviours at load time (PropSystem), so they need
nothing here. What is new:
- the fuse (backrooms:fuse): a ceramic cartridge fuse that brings a tripped section's lights back on;
- the wind-up alarm clock (backrooms:alarmclock-<side>): set it and it rings a while later, a lure left behind;
- the pillar light gone dark (backrooms:pillarlightdead): Level 1's pillar light when its breaker is tripped (the old block
  has no off state, and its code stays as it is);
- the sounds: the fire bell, the car alarm, the alarm clock's bells and its winding, a radio's static and music, the
  steam valve's warning hiss and its blast, and a breaker's fuse blowing.

Run from the repo root:  python tools/gen_props.py
"""
import json
import os
import re

import numpy as np
from PIL import Image, ImageDraw

from oggutil import write_ogg

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
LANG_PATH = os.path.join(ASSETS, "lang", "en.json")
RATE = 22050


def write_json(path, data, comment):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("// " + comment + "\n" + json.dumps(data, indent="\t") + "\n")


# ---------------------------------------------------------------- textures (32 px)

def noise_img(base, amount, seed, size=32):
    rng = np.random.default_rng(seed)
    a = np.array(base, dtype=np.float64)[None, None, :] * np.ones((size, size, 1))
    a += rng.normal(0, amount, (size, size, 1))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def textures():
    block = os.path.join(ASSETS, "textures", "block", "props")
    item = os.path.join(ASSETS, "textures", "item")
    os.makedirs(block, exist_ok=True)

    # The clock: red enamel worn at the edges, a cream face with its twelve marks and hands, brass bells and feet
    body = noise_img((168, 34, 30), 7, 1)
    d = ImageDraw.Draw(body)
    for i in range(32):
        d.point((i, 0), (120, 26, 24, 255)); d.point((i, 31), (120, 26, 24, 255))
    for x, y in ((3, 5), (25, 20), (14, 27), (28, 9)):
        d.ellipse((x, y, x + 2, y + 1), fill=(96, 84, 76, 255))  # chips in the enamel
    body.save(os.path.join(block, "alarmclock-body.png"))

    face = Image.new("RGBA", (32, 32), (226, 216, 186, 255))
    d = ImageDraw.Draw(face)
    d.ellipse((1, 1, 30, 30), outline=(150, 128, 70, 255), width=2)
    import math
    for h in range(12):
        a = h / 12 * 2 * math.pi
        x, y = 15.5 + 11.5 * math.sin(a), 15.5 - 11.5 * math.cos(a)
        r = 1.2 if h % 3 == 0 else 0.6
        d.ellipse((x - r, y - r, x + r, y + r), fill=(40, 34, 30, 255))
    d.line((16, 16, 16, 7), fill=(30, 26, 24, 255), width=2)     # the minute hand at twelve
    d.line((16, 16, 22, 19), fill=(30, 26, 24, 255), width=2)    # the hour hand at four
    d.line((16, 16, 9, 21), fill=(190, 40, 30, 255), width=1)    # the red alarm hand, set
    d.ellipse((14, 14, 17, 17), fill=(150, 128, 70, 255))
    face.save(os.path.join(block, "alarmclock-face.png"))

    brass = noise_img((178, 146, 70), 9, 2)
    d = ImageDraw.Draw(brass)
    for y in range(0, 32, 8):
        d.line((0, y, 31, y), fill=(214, 186, 110, 255))  # polished bands
    brass.save(os.path.join(block, "alarmclock-brass.png"))

    # The fuse: a white ceramic cartridge with a printed band, brass end caps
    fbody = noise_img((222, 220, 210), 4, 3)
    d = ImageDraw.Draw(fbody)
    d.rectangle((0, 12, 31, 19), fill=(46, 70, 132, 255))
    for x in range(3, 30, 6):
        d.rectangle((x, 14, x + 3, 17), fill=(230, 230, 230, 255))  # "30 A" in the band, as marks
    fbody.save(os.path.join(item, "fuse-body.png"))
    fcap = noise_img((186, 150, 74), 10, 4)
    fcap.save(os.path.join(item, "fuse-cap.png"))


# ---------------------------------------------------------------- shapes

DIRS = ("north", "east", "south", "west", "up", "down")


def bx(name, frm, to, tex, faces=DIRS, uv=None):
    (x1, y1, z1), (x2, y2, z2) = frm, to
    w, h, dd = x2 - x1, y2 - y1, z2 - z1
    sizes = {"north": (w, h), "south": (w, h), "east": (dd, h), "west": (dd, h), "up": (w, dd), "down": (w, dd)}
    out = {}
    for f in faces:
        a, b = sizes[f]
        out[f] = {"texture": "#" + tex, "uv": list(uv) if uv else [0, 0, min(16, max(a, 0.5)), min(16, max(b, 0.5))]}
    return {"name": name, "from": [x1, y1, z1], "to": [x2, y2, z2], "faces": out}


def shapes():
    # The alarm clock, its face to the north: a round-ish body (two boxes crossed), the face set into it, two bells on top
    # and the hammer between them, a winding key at the back, two feet
    els = [
        bx("Body", (5, 1.5, 6.5), (11, 7.5, 9.5), "body"),
        bx("BodyRound", (5.5, 1, 6.75), (10.5, 8, 9.25), "body"),
        bx("Face", (5.75, 2.25, 6.25), (10.25, 6.75, 6.5), "face", faces=("north",), uv=(0, 0, 16, 16)),
        bx("Rim", (5.5, 2, 6.0), (10.5, 2.25, 6.5), "brass"),
        bx("RimTop", (5.5, 6.75, 6.0), (10.5, 7.0, 6.5), "brass"),
        bx("BellLeft", (4.5, 7.5, 7.0), (7.0, 9.0, 9.0), "brass"),
        bx("BellRight", (9.0, 7.5, 7.0), (11.5, 9.0, 9.0), "brass"),
        bx("Stem", (7.75, 7.5, 7.75), (8.25, 9.5, 8.25), "brass"),
        bx("Hammer", (7.5, 9.0, 7.5), (8.5, 9.5, 8.5), "brass"),
        bx("Key", (7.25, 3.5, 9.5), (8.75, 5.0, 10.25), "brass"),
        bx("FootLeft", (5.5, 0, 7.25), (6.5, 1, 8.75), "brass"),
        bx("FootRight", (9.5, 0, 7.25), (10.5, 1, 8.75), "brass"),
    ]
    shape = {"textureWidth": 16, "textureHeight": 16,
             "textures": {"body": "backrooms:block/props/alarmclock-body", "face": "backrooms:block/props/alarmclock-face",
                          "brass": "backrooms:block/props/alarmclock-brass"},
             "elements": els}
    path = os.path.join(ASSETS, "shapes", "block", "props", "alarmclock.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(shape, indent="\t") + "\n")

    # The fuse, lying along X: a ceramic body between two brass caps (block space, an item shape)
    els = [
        bx("Body", (5, 0, 7), (11, 2, 9), "body"),
        bx("CapWest", (3.5, -0.25, 6.75), (5, 2.25, 9.25), "cap"),
        bx("CapEast", (11, -0.25, 6.75), (12.5, 2.25, 9.25), "cap"),
        bx("BladeWest", (2.5, 0.75, 7.75), (3.5, 1.25, 8.25), "cap"),
        bx("BladeEast", (12.5, 0.75, 7.75), (13.5, 1.25, 8.25), "cap"),
    ]
    for e in els:  # (lifted so the caps' undersides sit on the ground)
        e["from"][1] += 0.25
        e["to"][1] += 0.25
    shape = {"textureWidth": 16, "textureHeight": 16,
             "textures": {"body": "backrooms:item/fuse-body", "cap": "backrooms:item/fuse-cap"}, "elements": els}
    path = os.path.join(ASSETS, "shapes", "item", "fuse.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(shape, indent="\t") + "\n")


# ---------------------------------------------------------------- block and item types

ROTATE = {"north": 0, "east": 270, "south": 180, "west": 90}
METAL = {"walk": "game:walk/stone", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"}


def types():
    write_json(os.path.join(ASSETS, "blocktypes", "props", "alarmclock.json"), {
        "code": "alarmclock",
        "class": "BackroomsAlarmClock",
        "entityClass": "BackroomsAlarmClock",
        "variantgroups": [{"code": "side", "loadFromProperties": "abstract/horizontalorientation"}],
        "behaviors": [{"name": "HorizontalOrientable"}],
        "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]},
        "blockmaterial": "Metal",
        "drawtype": "json",
        "shapeByType": {f"*-{s}": {"base": "block/props/alarmclock", "rotateY": r} for s, r in ROTATE.items()},
        "sidesolid": {"all": False},
        "sideopaque": {"all": False},
        "lightAbsorption": 0,
        "resistance": 0.4,
        "maxStackSize": 4,
        "replaceable": 100,
        "collisionbox": {"x1": 0.3, "y1": 0, "z1": 0.375, "x2": 0.7, "y2": 0.6, "z2": 0.625},
        "selectionbox": {"x1": 0.25, "y1": 0, "z1": 0.35, "x2": 0.75, "y2": 0.625, "z2": 0.65},
        "sounds": {"place": "game:block/ingot", "break": "game:block/ingot", "hit": "game:block/ingot"},
        "guiTransform": {"rotation": {"x": -22, "y": -45, "z": 0}, "origin": {"x": 0.5, "y": 0.3, "z": 0.5}, "scale": 2.4},
        "fpHandTransform": {"translation": {"x": 0, "y": 0.2, "z": 0.3}, "rotation": {"x": 0, "y": -40, "z": 0}, "scale": 1.6},
        "tpHandTransform": {"translation": {"x": -0.9, "y": -0.4, "z": -0.6}, "rotation": {"x": 0, "y": -45, "z": 0}, "scale": 0.7},
        "groundTransform": {"origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 2.4},
    }, "A wind-up alarm clock (src/Props/AlarmClock.cs): set it down, wind and set it, and it rings a while later; a lure left behind")

    write_json(os.path.join(ASSETS, "blocktypes", "level1", "pillarlightdead.json"), {
        "code": "pillarlightdead",
        "creativeinventory": {"general": ["*"], "decorative": ["*"]},
        "blockmaterial": "Stone",
        "drawtype": "json",
        "shape": {"base": "block/pillarlight"},
        "textures": {"tube": {"base": "block/props/tube-off"}},
        "resistance": 8,
        "requiredMiningTier": 3,
        "sounds": {"walk": "game:walk/stone", "place": "game:block/glass", "break": "game:block/glass", "hit": "game:block/glass"},
    }, "Level 1's pillar light with its breaker tripped (src/Props/Breakers.cs): the same pillar, its tubes dead (it breaks down as the building does). The lit pillar light has no off state of its own")

    write_json(os.path.join(ASSETS, "itemtypes", "props", "fuse.json"), {
        "code": "fuse",
        "maxstacksize": 8,
        "shape": {"base": "item/fuse"},
        "creativeinventory": {"general": ["*"], "items": ["*"], "backrooms": ["*"]},
        "materialDensity": 2000,
        "behaviors": [{"name": "GroundStorable", "properties": {
            "layout": "Quadrants",
            "collisionBox": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.125, "z2": 1}}}],
        "guiTransform": {"rotation": {"x": -30, "y": 30, "z": 0}, "origin": {"x": 0.5, "y": 0.1, "z": 0.5}, "scale": 3.2},
        "fpHandTransform": {"translation": {"x": 0, "y": 0.2, "z": 0.3}, "rotation": {"x": 0, "y": 60, "z": -20}, "scale": 2.2},
        "tpHandTransform": {"translation": {"x": -0.8, "y": -0.2, "z": -0.6}, "rotation": {"x": 0, "y": 0, "z": -60}, "scale": 0.8},
        "groundTransform": {"origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 3.0},
    }, "A fuse (src/Props/Breakers.cs): fitted in a tripped breaker box or electrical panel, it brings that section's lights back on")


# ---------------------------------------------------------------- sounds

def t_of(seconds):
    return np.arange(int(seconds * RATE)) / RATE


def norm(signal, peak):
    signal = np.asarray(signal, dtype=np.float64)
    return peak * signal / max(1e-9, np.max(np.abs(signal)))


def bandpass(signal, lo, hi):
    spec = np.fft.rfft(signal)
    f = np.fft.rfftfreq(len(signal), 1 / RATE)
    spec[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(spec, len(signal))


def strikes(seconds, rate, partials, decay, jitter=0.0, seed=0, start=0.0):
    """A bell struck rate times a second: each strike a sum of decaying partials (freq, amp)."""
    rng = np.random.default_rng(seed)
    n = int(seconds * RATE)
    out = np.zeros(n)
    tail = int(decay * 6 * RATE)
    tt = np.arange(tail) / RATE
    env = np.exp(-tt / decay)
    one = sum(a * np.sin(2 * np.pi * f * tt) for f, a in partials) * env
    k = 0
    while True:
        at = start + k / rate + (rng.uniform(-jitter, jitter) if jitter else 0)
        i = int(at * RATE)
        if i >= n:
            break
        if i >= 0:
            m = min(tail, n - i)
            out[i:i + m] += one[:m] * (0.85 + 0.15 * rng.random())
        k += 1
    return out


def sounds():
    out = os.path.join(ASSETS, "sounds", "effect", "props")
    os.makedirs(out, exist_ok=True)
    rng = np.random.default_rng(7)

    def save(name, signal, peak=0.9, fade=0.004):
        signal = norm(signal, peak)
        k = int(fade * RATE)
        if k:
            signal[:k] *= np.linspace(0, 1, k)
            signal[-k:] *= np.linspace(1, 0, k)
        if write_ogg(os.path.join(out, name + ".ogg"), signal, RATE):
            print("wrote sounds/effect/props/" + name + ".ogg")

    # The fire bell: an electric bell's hammer, 18 strikes a second on a steel gong (2 s, it loops seamlessly: whole strikes,
    # the clip cut from the middle of a longer run so every strike's ring carries over the seam)
    long = strikes(4.0, 18, [(1180, 1.0), (2950, 0.45), (5100, 0.2), (7300, 0.08)], 0.05, seed=1)
    bell = long[RATE:3 * RATE]
    bell += 0.04 * bandpass(rng.normal(0, 1, len(bell)), 2000, 6000)  # the buzz of the striker
    save("firebell", bell, 0.95, fade=0)

    # The car alarm: a rising whoop, then a two-tone yelp (2 s)
    t = t_of(1.0)
    f = 650 + 900 * t
    whoop = np.sign(np.sin(2 * np.pi * np.cumsum(f) / RATE)) * 0.6 + np.sin(2 * np.pi * np.cumsum(f) / RATE) * 0.4
    t2 = t_of(1.0)
    f2 = np.where((t2 * 8).astype(int) % 2 == 0, 1350, 950)
    yelp = np.sign(np.sin(2 * np.pi * np.cumsum(f2) / RATE)) * 0.6 + np.sin(2 * np.pi * np.cumsum(f2) / RATE) * 0.4
    car = bandpass(np.concatenate([whoop, yelp]), 300, 5000)
    save("caralarm", car, 0.95)

    # The alarm clock: a hammer between two small bells, 24 a second, for 0.8 s, then a breath (1 s)
    ring = strikes(0.8, 24, [(2350, 1.0), (5600, 0.3)], 0.03, seed=2) + strikes(0.8, 24, [(2780, 0.9), (6400, 0.25)], 0.03, seed=3, start=1 / 48)
    save("alarmclock", np.concatenate([ring, np.zeros(int(0.2 * RATE))]), 0.9)

    # Winding it: a ratchet, eight clicks
    wind = strikes(0.6, 13, [(3200, 1.0), (7000, 0.5)], 0.006, jitter=0.01, seed=4)
    wind += 0.3 * strikes(0.6, 13, [(900, 1.0)], 0.01, jitter=0.01, seed=5)
    save("windup", wind, 0.7)

    # A radio: static, crackles, and a station half tuned in under it (a slow tune, wobbling in and out) (4 s)
    t = t_of(4.0)
    static = bandpass(rng.normal(0, 1, len(t)), 400, 5000) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.37 * t) ** 2)
    for _ in range(40):
        i = rng.integers(0, len(t) - 200)
        static[i:i + 60] += rng.normal(0, 4, 60)
    notes = [392, 440, 494, 440, 392, 330, 349, 392]
    tune = np.zeros(len(t))
    for k, nf in enumerate(notes):
        i, m = int(k * 0.5 * RATE), int(0.48 * RATE)
        tt = np.arange(m) / RATE
        tune[i:i + m] += (np.sin(2 * np.pi * nf * tt) + 0.3 * np.sin(4 * np.pi * nf * tt)) * np.exp(-tt * 2.5)
    tune = bandpass(tune, 300, 3000) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.21 * t + 1.0))
    save("radio", 0.55 * static / np.max(np.abs(static)) + 0.6 * tune / np.max(np.abs(tune)), 0.85, fade=0.01)

    # The valve's warning: a hiss rising over a second as the pressure comes
    t = t_of(1.0)
    warn = bandpass(rng.normal(0, 1, len(t)), 2500, 9000) * np.linspace(0.05, 1, len(t)) ** 1.5
    warn += 0.3 * bandpass(rng.normal(0, 1, len(t)), 200, 900) * np.linspace(0, 1, len(t))
    save("steamwarn", warn, 0.8)

    # The blast: a full roar of steam (1 s, repeated while the jet runs)
    t = t_of(1.0)
    blast = bandpass(rng.normal(0, 1, len(t)), 1500, 10000) + 0.7 * bandpass(rng.normal(0, 1, len(t)), 80, 800)
    blast *= 0.9 + 0.1 * np.sin(2 * np.pi * 7 * t)
    save("steamblast", blast, 0.95, fade=0.02)

    # A fuse blowing: a bang, a crackle of sparks and the hum of the mains dying away (0.9 s)
    t = t_of(0.9)
    bang = rng.normal(0, 1, len(t)) * np.exp(-t / 0.02) + np.sin(2 * np.pi * 70 * t) * np.exp(-t / 0.06) * 1.5
    crackle = np.zeros(len(t))
    for _ in range(26):
        i = rng.integers(int(0.03 * RATE), int(0.5 * RATE))
        crackle[i:i + 40] += rng.normal(0, 1.2, 40)
    hum = (np.sin(2 * np.pi * 100 * t) + 0.5 * np.sin(2 * np.pi * 200 * t)) * np.exp(-t / 0.25) * 0.25
    save("fusepop", bang + crackle + hum, 0.95)


# ---------------------------------------------------------------- lang

LANG = {
    "item-fuse": "Fuse",
    "itemdesc-fuse": "A ceramic cartridge fuse, thirty amps, still in its paper. Hold it and right-click a tripped breaker box or electrical panel to bring that section's lights back on. Turns up now and then in toolboxes, tool shelves, maintenance shelving and machine cabinets.",
    "block-alarmclock-*": "Wind-up Alarm Clock",
    "blockdesc-alarmclock-*": "Twin bells on top, a key in the back. Set it down and right-click to wind and set it: it rings twenty seconds later (each right-click while it ticks adds twenty, up to two minutes), loud enough to bring whatever hears it to it. The old spring holds only so many windings.",
    "block-pillarlightdead": "Pillar Light",
    "blockhelp-pullalarm": "Pull the alarm",
    "blockhelp-testbell": "Press the test button",
    "blockhelp-turnvalve": "Turn the valve",
    "blockhelp-tripbreaker": "Throw the main switch",
    "blockhelp-fitfuse": "Fit a fuse",
    "blockhelp-strikecar": "Strike the car",
    "blockhelp-windclock": "Wind and set",
    "blockhelp-radioon": "Turn on",
    "blockhelp-radiooff": "Turn off",
    "props-alarm-reset": "The handle is down and its glass rod broken. It will be reset in {0} minutes.",
    "props-alarm-ringing": "It is ringing already.",
    "props-valve-building": "The wheel turns freely: no pressure yet. Try again in {0} seconds.",
    "props-valve-venting": "It is venting already.",
    "props-breaker-tripped": "The fuse blows with a bang and the lights die.",
    "props-breaker-dark": "The main switch is thrown and the fuse is blown. It needs a new fuse.",
    "props-breaker-restored": "The new fuse holds. The lights flicker back on.",
    "props-breaker-nolights": "The switch drops with a clunk, but nothing round here goes dark.",
    "props-car-dead": "The alarm only clicks: the battery needs a while.",
    "props-car-burnt": "Burnt out. Nothing in it works.",
    "props-clock-set": "Wound and set: it rings in {0} seconds.",
    "props-clock-ringing": "It is ringing.",
    "props-clock-spent": "The spring has snapped. It will not ring again.",
    "props-radio-on": "Static, and somewhere under it a tune.",
    "props-radio-off": "Off.",
    "props-info-alarmreset": "Pulled; reset in {0} min",
    "props-info-dark": "Tripped: needs a fuse (or the power comes back by itself in about {0} in-game hours)",
    "props-info-clockwinds": "Windings left: {0}",
    "props-info-clockset": "Set: rings in {0} s",
    "props-info-clockspent": "The spring has snapped",
}


def merge_lang():
    """Updates these keys in lang/en.json in place and appends the new ones at the end (the file is otherwise untouched)."""
    with open(LANG_PATH, encoding="utf-8", newline="") as f:
        text = f.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    new_lines = []
    for key, value in LANG.items():
        line = "\t" + json.dumps(key) + ": " + json.dumps(value, ensure_ascii=False)
        pattern = re.compile("^\t" + re.escape(json.dumps(key)) + r":.*?(,?)\r?$", re.M)
        if pattern.search(text):
            text = pattern.sub(lambda m: line + m.group(1), text, count=1)
        else:
            new_lines.append(line)
    if new_lines:
        body = text.rstrip().rpartition("}")[0].rstrip()
        if not body.endswith(",") and not body.endswith("{"):
            body += ","
        text = body + nl + nl + ("," + nl).join(new_lines) + nl + "}" + nl
    json.loads(text)  # still valid
    with open(LANG_PATH, "w", encoding="utf-8", newline="") as f:
        f.write(text)


if __name__ == "__main__":
    textures()
    shapes()
    types()
    sounds()
    merge_lang()
