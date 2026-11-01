"""Level 31, "Roller Rink": its ways in and out (the links round, 2026-10-31; docs/design/experimental-levels/LINKS.md).

It writes only its own files, none of the ones the other gen_31 scripts write:
    blocktypes/31/  l31-door (lower, upper x ns, we): a varnished wooden panel door, a threshold (kind l31-door): in a
                    wall of Level 2, 3 or 6 it opens on a lobby of the rink; in a lobby it is the way back
                    l31-revolvingdoor (side, center, top x facing): Level 3999's revolving door (its shapes), the rink's
                    own threshold (kind l31-revolving): out to Level 9, 10 or 11
    textures/block/31/  door-lower, door-upper, door-edge
    sounds/ambient/31/doorpop.ogg   2000s bubblegum pop, faint, as heard through a wooden door (looping, 15 s)
    lang/en.json    the lines of the ways in and out, in the level's block (with gen_31_content.py's merge); and the
                    Coach's talk again (gen_31_content.dialogue: his "lead me out" now walks you to a revolving door)

Run from the repo root:
    bash tools/locked.sh run python tools/gen_31_links.py
"""
import json
import os
import re
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gen_31_content as C  # noqa: E402
from gen_31 import write_json, save, tex, lowpass_circular, WOOD, BLOCKS, ASSETS, ROOT  # noqa: E402
from oggutil import write_ogg  # noqa: E402
from gen_entity_sounds import RATE  # noqa: E402
from texlib import S  # noqa: E402


# ======================================================================== The wooden door

OAK = (150, 98, 52)


def clamp(v):
    return max(0, min(255, int(round(v))))


def wood_grain(rng, w, h, base, streak=0.08):
    """Vertical oak grain: a base colour with long darker streaks and a little noise, as an array (h, w, 3)."""
    img = np.zeros((h, w, 3))
    cols = rng.uniform(-1, 1, size=w)
    cols = np.convolve(cols, [0.25, 0.5, 0.25], mode="same")
    for y in range(h):
        for x in range(w):
            k = 1 + streak * cols[x] + 0.03 * rng.uniform(-1, 1) + 0.04 * np.sin((y + 7 * cols[x]) * 0.7 + x * 0.3)
            img[y, x] = [c * k for c in base]
    return img


def door_textures():
    """The face of a varnished four-panel door, 32 px a block: the lower half (two panels, the brass knob and its keyhole
    near the top on the right) and the upper (two panels under the head of the frame); and the plain oak of its edge."""
    nrng = np.random.default_rng(3131)

    def face(upper):
        a = wood_grain(nrng, S, S, OAK)
        img = Image.new("RGBA", (S, S))
        px = img.load()
        frame = 2  # the casing round the door, darker
        for y in range(S):
            for x in range(S):
                r, g, b = a[y, x]
                k = 1.0
                # The casing down both sides (and across the top of the upper half)
                if x < frame or x >= S - frame or upper and y < frame:
                    k = 0.62
                else:
                    # Two raised panels side by side, each with a bevelled edge: rails at the top and bottom of each half
                    lx = x - frame
                    inner_w = S - 2 * frame
                    col = 0 if lx < inner_w // 2 else 1
                    px0 = 3 if col == 0 else inner_w // 2 + 2
                    px1 = inner_w // 2 - 3 if col == 0 else inner_w - 4
                    py0 = (frame + 4) if upper else 3
                    py1 = S - 3 if upper else S - 6
                    inside = px0 <= lx <= px1 and py0 <= y <= py1
                    edge = inside and (lx in (px0, px1) or y in (py0, py1))
                    if edge:
                        k = 0.78 if (lx == px0 or y == py0) else 1.18
                    elif inside:
                        k = 1.06
                px[x, y] = (clamp(r * k), clamp(g * k), clamp(b * k), 255)
        # The varnish: a soft highlight down the left third
        for y in range(S):
            for x in range(frame, S - frame):
                hl = max(0.0, 1 - abs(x - S * 0.32) / 5) * 0.10
                r, g, b, _ = px[x, y]
                px[x, y] = (clamp(r + 255 * hl * 0.6), clamp(g + 255 * hl * 0.5), clamp(b + 255 * hl * 0.3), 255)
        if not upper:
            # The brass knob, at about a metre: near the top of the lower half, on the right, and the keyhole under it
            for (dx, dy, c) in ((0, 0, (212, 172, 74)), (1, 0, (236, 204, 110)), (0, 1, (170, 128, 46)), (1, 1, (196, 150, 58)),
                                (-1, 0, (180, 138, 52)), (0, -1, (226, 190, 92)), (1, -1, (240, 214, 130)), (-1, 1, (150, 110, 40))):
                px[S - 7 + dx, 6 + dy] = c + (255,)
            px[S - 7, 10] = (40, 26, 14, 255)
            px[S - 7, 11] = (52, 34, 18, 255)
            # A kick plate's worn edge along the bottom
            for x in range(frame, S - frame):
                r, g, b, _ = px[x, S - 2]
                px[x, S - 2] = (clamp(r * 0.8), clamp(g * 0.8), clamp(b * 0.8), 255)
        return img

    save(face(False), "door-lower")
    save(face(True), "door-upper")
    edge = wood_grain(nrng, S, S, (130, 84, 44), streak=0.06)
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            px[x, y] = tuple(clamp(v) for v in edge[y, x]) + (255,)
    save(img, "door-edge")


def door_block():
    textures = {}
    for part in ("lower", "upper"):
        for axis, faces in (("ns", ("north", "south")), ("we", ("east", "west"))):
            t = {"all": tex("door-edge")}
            for f in faces:
                t[f] = tex("door-" + part)
            textures[f"*-{part}-{axis}"] = t
    data = {
        "code": "l31-door",
        "variantgroups": [{"code": "part", "states": ["lower", "upper"]}, {"code": "axis", "states": ["ns", "we"]}],
        "texturesByType": textures,
        "creativeinventory": {"general": ["*-lower-ns"], "backrooms": ["*-lower-ns"]},
        "blockmaterial": "Wood", "drawtype": "cube", "lightAbsorption": 99, "resistance": 99999, "drops": [], "sounds": WOOD,
        "behaviors": [{"name": "BackroomsThreshold", "properties": {"kind": "l31-door"}}],
    }
    write_json(os.path.join(BLOCKS, "l31-door.json"), data,
               "Level 31: a varnished wooden panel door (lower and upper halves; its face on the north and south faces, or east and west). "
               "In a wall of Level 2, 3 or 6, with pop music playing faintly behind it, it opens on a lobby of the roller rink; in a "
               "lobby it is the way back (threshold kind l31-door)")


def revolving_block():
    """Level 3999's revolving door, the drum and its invisible fillers, as the rink's own block: the same shapes, another kind."""
    path = os.path.join(ASSETS, "blocktypes", "3999", "l3999-revolvingdoor.json")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    data = json.loads(re.sub(r"^\s*//.*$", "", text, flags=re.M))
    out = json.loads(json.dumps(data).replace("l3999-revolvingdoor-", "l31-revolvingdoor-"))
    out["code"] = "l31-revolvingdoor"
    out["behaviors"] = [{"name": "BackroomsThreshold", "properties": {"kind": "l31-revolving"}}]
    out.pop("attributes", None)
    out["resistance"] = 99999
    out["creativeinventory"] = {"general": ["l31-revolvingdoor-center-north"], "backrooms": ["l31-revolvingdoor-center-north"]}
    write_json(os.path.join(BLOCKS, "l31-revolvingdoor.json"), out,
               "Level 31: the Revolving Door (Fandom), 3 wide and 3 high in the front wall of one lobby in twelve: Level 3999's drum of "
               "glass wings (its shapes; center draws the whole of it, side and top are invisible collision). Use it to go through, "
               "out to Level 9, 10 or 11, the same one every time (threshold kind l31-revolving)")


# ======================================================================== The music behind the door

def doorpop():
    """Eight bars of 2000s bubblegum pop at 128 bpm (15 s, looping): four on the floor, claps on two and four, a bouncy octave
    bass, bright offbeat synth stabs and a sing-song lead; then as heard through a wooden door, from a room away: the top
    end gone, the kick and the bass thumping through, a little of the door's own boom."""
    rng = np.random.default_rng(3132)
    bpm = 128
    beat = 60 / bpm
    bars = 8
    n = int(round(bars * 4 * beat * RATE))
    out = np.zeros(n)

    def add(sound, at):
        i = int(at * RATE) % n
        j = min(n, i + len(sound))
        out[i:j] += sound[: j - i]
        if i + len(sound) > n:
            out[: i + len(sound) - n] += sound[j - i:]

    def hz(midi):
        return 440 * 2 ** ((midi - 69) / 12)

    # vi - IV - I - V in E major: C#m, A, E, B (a bar each, twice)
    chords = [(49, [61, 64, 68]), (45, [61, 64, 69]), (40, [59, 64, 68]), (47, [59, 63, 66])]
    for bar in range(bars):
        root, triad = chords[bar % 4]
        at = bar * 4 * beat
        for b in range(4):
            tk = np.arange(int(0.22 * RATE)) / RATE
            kick = np.sin(2 * np.pi * np.cumsum(48 + 110 * np.exp(-tk * 35)) / RATE) * np.exp(-tk * 10) * 0.8
            add(kick, at + b * beat)
            if b % 2:
                tc = np.arange(int(0.12 * RATE)) / RATE
                clap = rng.normal(size=len(tc)) * (np.exp(-tc * 30) + 0.5 * np.exp(-np.maximum(0, tc - 0.012) * 30) * (tc > 0.012)) * 0.22
                add(clap, at + b * beat)
        for e in range(8):
            t8 = np.arange(int(beat / 2 * RATE)) / RATE
            # The octave bass, bouncing root-octave on eighths
            f = hz(root - 12 + (12 if e % 2 else 0))
            bass = np.sin(2 * np.pi * f * t8) * np.exp(-t8 * 5) * 0.45 + (2 * ((f * t8) % 1) - 1) * np.exp(-t8 * 9) * 0.12
            add(bass, at + e * beat / 2)
            # Bright stabs on the off-eighths
            if e % 2:
                ts = np.arange(int(0.11 * RATE)) / RATE
                stab = sum((2 * ((hz(m) * (1 + d) * ts) % 1) - 1) for m in triad for d in (-0.006, 0.006)) * np.exp(-ts * 22) * 0.05
                add(stab, at + e * beat / 2)
    # The sing-song lead: a "voice" of two formants over a pulse, a hook that goes up and comes back down
    hook = [76, 76, 78, 80, None, 80, 78, 76, 73, None, 73, 75, 76, None, 75, 73,
            71, 71, 73, 76, None, 76, 75, 73, 71, None, 68, 71, 73, None, None, None]
    for k, m in enumerate(hook):
        if m is None:
            continue
        at = k * beat
        tl = np.arange(int(beat * 0.85 * RATE)) / RATE
        f = hz(m) * (1 + 0.006 * np.sin(2 * np.pi * 5.5 * tl))
        ph = np.cumsum(f) / RATE
        pulse = np.where((ph % 1) < 0.35, 1.0, -1.0)
        vowel = np.sin(2 * np.pi * 700 * tl) * 0.3 + np.sin(2 * np.pi * 1150 * tl) * 0.2
        voice = pulse * (1 + 0.6 * vowel) * np.minimum(1, tl / 0.02) * np.minimum(1, (beat * 0.85 - tl) / 0.05) * 0.10
        add(voice, at)
    # Through the door: the top end gone, the boom of the panel
    sig = lowpass_circular(out, 520, slope=2.5)
    spec = np.fft.rfft(sig)
    fr = np.fft.rfftfreq(len(sig), 1 / RATE)
    spec *= 1 + 0.8 * np.exp(-((fr - 110) / 40) ** 2)  # the door's boom
    sig = np.fft.irfft(spec, n=len(sig))
    sig += 0.002 * lowpass_circular(rng.normal(size=n), 2000)
    sig = 0.55 * sig / max(1e-9, np.max(np.abs(sig)))
    path = os.path.join(ASSETS, "sounds", "ambient", "31", "doorpop.ogg")
    if write_ogg(path, sig, RATE):
        print("wrote", os.path.relpath(path, ROOT))


# ======================================================================== Words

def words():
    C.LANG.update({
        "block-l31-door-*": "Wooden Door",
        "block-l31-revolvingdoor-*": "Revolving Door",
        "blockhelp-l31-skateshelf": "Take a pair of skates",
        # The ways in and out (Thresholds/ThresholdNetwork.L31.cs, Regions/L31System.cs)
        "l31-door-arrive": "The door swings shut behind you on a roller rink's lobby, and the music that was behind it is all round you now.",
        "l31-door-back": "You push the wooden door open. The music shuts off behind you like a radio.",
        "l31-revolving-out": "You push, and the glass turns, and turns, and lets you out somewhere else.",
        "l31-skates-take": "You lift a pair of skates out of the cubbies. Nobody stops you. Nobody is looking.",
        "l31-skates-have": "You already have a pair of skates from the cubbies.",
        "l31-skates-noclip": "The floor gives under the skates, and then the skates are gone, and so is the rink. Yellow wallpaper. A hum. You are in your socks.",
        "l31-coach-leadout": "The Coach walks you to the nearest revolving door and leaves it marked on your map.",
        "l31-coach-leadout-none": "The Coach frowns. \"There's none near enough to walk to. Keep to the halls and look in the lobbies; one turns up.\"",
        "l31-waypoint-revolving": "Revolving Door (Level 31): out",
    })


def merge_lang():
    """Puts the lines into en.json: a key already there (anywhere in the level's lines, which other blocks' lines split in
    two) is updated in place; a new one goes after the last of the level's lines from gen_31_content.py."""
    with open(C.EN, encoding="utf-8") as f:
        lines = f.read().split("\n")
    where = {}
    for i, l in enumerate(lines):
        m = re.match(r'^\t"([^"]+)"\s*:', l)
        if m:
            where[m.group(1)] = i
    anchor = where["l31-skates-on"]
    new = []
    for k, v in C.LANG.items():
        entry = "\t" + json.dumps(k) + ": " + json.dumps(v, ensure_ascii=False)
        if k in where:
            i = where[k]
            lines[i] = entry + ("," if lines[i].rstrip().endswith(",") else "")
        else:
            new.append(entry + ",")
    lines[anchor + 1:anchor + 1] = new
    text = "\n".join(lines)
    json.loads(text)
    with open(C.EN, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("wrote", os.path.relpath(C.EN, ROOT), f"({len(C.LANG)} Level 31 lines, {len(new)} new)")


def main():
    door_textures()
    door_block()
    revolving_block()
    doorpop()
    C.dialogue()
    words()
    merge_lang()


if __name__ == "__main__":
    main()
