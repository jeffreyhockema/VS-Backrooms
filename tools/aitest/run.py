"""Headless perception tests (entity AI overhaul, batch P0; docs/design/entity-ai-overhaul/README.md, 4.5).

Starts a dedicated server with the built mod, puts straw dummies and a Hound down with `/backrooms dummy ...` and
`/backrooms perceive ...`, parses the `[backrooms] perceive` log lines and asserts what the Hound sees, hears and
senses.

    python tools/aitest/run.py --mods <Mods dir> [--data <dir>] [--keep] [--only <test>[,<test>]]

Exits non-zero if any case fails. The full console log goes to <data>/aitest.log.
"""
import argparse
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time

LEVEL = "6"          # a dark level (no lamps)
ENTITY = "hound"

START_RE = re.compile(r"perceive (\w+)#(\d+) start: ([\d.]+) blocks from \w+ #(\d+), facing (\w+), line (\w+), light on target (-?\d+)")
STEP_RE = re.compile(r"perceive (\w+)#(\d+) t=(\d+) d=([\d.]+) light=(-?\d+) held=(\d+)(?: sneaking)?(?: running)? -> (None|Heard|Sensed|Seen) (.*?) \| belief (\w+) conf ([\d.]+) err (\S+)")
DONE_RE = re.compile(r"perceive (\w+)#(\d+) done: seen (\d+)/(\d+), sensed (\d+), heard (\d+), first seen t=(-?\d+), lost t=(-?\d+)")
DUMMY_RE = re.compile(r"Dummy #(\d+) at (-?\d+) (-?\d+) (-?\d+), Level (\S+), light (-?\d+)")


class ServerDied(Exception):
    pass


class Server:
    def __init__(self, mods, data, port=42733):
        self.lines = []
        self.lock = threading.Lock()
        self.ready = threading.Event()
        exe = self.find_server()
        cfg = "{ Port: %d, WorldConfig: { Seed: '12345', WorldType: 'backrooms', PlayStyle: 'backrooms' } }" % port
        self.p = subprocess.Popen([exe, "--dataPath", data, "--addModPath", mods.replace("\\", "/"), "--withconfig", cfg],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
        threading.Thread(target=self.read, daemon=True).start()

    @staticmethod
    def find_server():
        for base in (os.environ.get("VINTAGE_STORY"), os.path.join(os.environ.get("APPDATA", ""), "Vintagestory"), r"G:\Games\Vintagestory"):
            if base and os.path.exists(os.path.join(base, "VintagestoryServer.exe")):
                return os.path.join(base, "VintagestoryServer.exe")
        raise SystemExit("VintagestoryServer.exe not found (set VINTAGE_STORY)")

    def read(self):
        for raw in iter(self.p.stdout.readline, b""):
            s = raw.decode("utf-8", "replace").rstrip()
            with self.lock:
                self.lines.append(s)
            if "Dedicated Server now running" in s or "Server running" in s:
                if not self.ready.is_set(): self.boot_end = len(self.lines)
                self.ready.set()

    def mark(self):
        with self.lock:
            return len(self.lines)

    def since(self, mark):
        with self.lock:
            return list(self.lines[mark:])

    def cmd(self, c):
        with self.lock:
            self.lines.append(">>> " + c)
        if self.p.poll() is not None:
            raise ServerDied("server exited with code %s" % self.p.returncode)
        try:
            self.p.stdin.write((c + chr(13) + chr(10)).encode("utf-8"))
            self.p.stdin.flush()
        except OSError as e:
            raise ServerDied("server stdin closed (%r), exit code %s" % (e, self.p.poll()))

    def wait(self, pred, mark, timeout):
        """Waits for a line after `mark` for which pred(line) is truthy; returns that value or None."""
        end = time.time() + timeout
        seen = mark
        while time.time() < end:
            with self.lock:
                chunk = self.lines[seen:]
                seen += len(chunk)
            for line in chunk:
                r = pred(line)
                if r:
                    return r
            if self.p.poll() is not None:
                raise ServerDied("server exited with code %s" % self.p.returncode)
            time.sleep(0.1)
        return None

    def stop(self):
        try:
            self.cmd("/stop")
            self.p.wait(240)
        except Exception:  # noqa: BLE001
            self.p.kill()


class Probe:
    """One running perceive probe: parses its lines out of the console as they come."""

    def __init__(self, srv, start):
        self.srv, self.ent = srv, start.group(2)
        self.clear = start.group(6) == "clear"
        self.dist = float(start.group(3))

    def steps(self):
        out = {}
        for line in self.srv.since(0):
            m = STEP_RE.search(line)
            if m and m.group(2) == self.ent:
                out[int(m.group(3))] = (m.group(7), m.group(8), float(m.group(10)))
        return out

    def t(self):
        s = self.steps()
        return max(s) if s else 0

    def wait_t(self, t, timeout=40):
        end = time.time() + timeout
        while time.time() < end and self.t() < t and self.done() is None:
            time.sleep(0.2)

    def done(self):
        for line in self.srv.since(0):
            m = DONE_RE.search(line)
            if m and m.group(2) == self.ent:
                return {"seen": int(m.group(3)), "steps": int(m.group(4)), "sensed": int(m.group(5)), "heard": int(m.group(6)),
                        "first": int(m.group(7)), "lost": int(m.group(8))}
        return None

    def wait_done(self, timeout=60):
        end = time.time() + timeout
        while time.time() < end:
            d = self.done()
            if d:
                return d
            time.sleep(0.3)
        return None

    def contacts(self, lo=0, hi=10 ** 6):
        return {t: v[0] for t, v in self.steps().items() if lo <= t <= hi}

    def count(self, what, lo=0, hi=10 ** 6):
        return sum(1 for c in self.contacts(lo, hi).values() if c == what)

    def timeline(self):
        c = self.contacts()
        return "".join({"Seen": "S", "Sensed": "s", "Heard": "h", "None": "."}[c[t]] for t in sorted(c))


class NoSpot(RuntimeError):
    pass


class Ctx:
    def __init__(self, srv):
        self.srv = srv
        self.good = {}        # distance -> dummy key giving a clear line at that distance

    def reset(self):
        self.srv.cmd("/backrooms perceive stop")
        time.sleep(0.5)
        self.srv.cmd("/backrooms dummy remove")
        time.sleep(0.5)

    def place(self, key=None, level=LEVEL):
        """Places a dummy; retries while chunks load. Returns (key, light)."""
        k = key
        for attempt in range(8):
            if k is None:
                k = int(time.time() * 1000) % 100000
            m = self.srv.mark()
            self.srv.cmd("/backrooms dummy place %s %d" % (level, k))
            r = self.srv.wait(lambda l: DUMMY_RE.search(l) or ("not loaded" in l.lower() and l) or ("Found nowhere" in l and l), m, 20)
            if hasattr(r, "group"):
                return k, int(r.group(6))
            time.sleep(10 if r else 3)
            if attempt >= 3 and key is None:
                k = None
        raise RuntimeError("could not place a dummy in Level " + level)

    def perceive(self, dist, seconds, facing="toward", overrides=""):
        """Starts a probe; retries while chunks around the spot load."""
        tries = 6
        while tries > 0:
            m = self.srv.mark()
            self.srv.cmd("/backrooms perceive %s %d %d %s %s" % (ENTITY, dist, seconds, facing, overrides))
            start = self.srv.wait(lambda l: START_RE.search(l) or ("No floor" in l and l), m, 15)
            if hasattr(start, "group"):
                return Probe(self.srv, start)
            if start:   # no floor out there: its chunks are not loaded (they may stay so): give up on this spot early
                tries -= 1
                if tries <= 4:
                    break
            time.sleep(8)
        raise NoSpot("perceive did not start at %d blocks" % dist)

    def far(self, dist, light=0, fallback=(), level=LEVEL):
        """Leaves a dummy placed in the dark level with a clear line at `dist` (else a fallback distance) and no probe
        running; returns (dummy light, distance used)."""
        for d in (dist,) + tuple(fallback):
            known = self.good.get(d)
            keys = [known] if known else [None] * 8
            for k in keys:
                self.reset()
                key, dl = self.place(k, level)
                if dl >= 4:
                    continue
                try:
                    p = self.perceive(d, 1, "toward")
                except NoSpot:
                    continue
                p.wait_done(10)
                self.srv.cmd("/backrooms perceive stop")
                if p.clear:
                    self.good[d] = key
                    self.reset()
                    key, dl = self.place(key, level)
                    if light:
                        self.srv.cmd("/backrooms dummy light %d" % light)
                        time.sleep(0.5)
                    return dl, d
        raise RuntimeError("no clear line of %d blocks found in Level %s" % (dist, level))


# ---------------------------------------------------------------- the cases
# Ranges for the Hound: dark 8, lit 40, carried light x1.5 at held light >= 14 (so 60 lit), sneaking x0.5 (so 30 lit with a
# torch), hearing 32 (a noise of loudness l is heard within 32*l), running heard within 32*0.4 = 12.8, fear sense 12 below
# stability 0.4, memory 8 s.

def t_dark_far(c):
    dl, d = c.far(20, fallback=(16,))
    p = c.perceive(d, 10)
    done = p.wait_done()
    seen = p.count("Seen")
    note = "" if d == 20 else " (FELL BACK to %d blocks: no clear 20-block line)" % d
    return bool(done) and p.clear and seen == 0, "dummy light %d, %d blocks, line clear=%s, timeline %s, seen %d/10%s" % (dl, d, p.clear, p.timeline(), seen, note)


def t_lit_far(c):
    dl, d = c.far(20, light=14, fallback=(16,))
    p = c.perceive(d, 6)
    done = p.wait_done()
    first = done["first"] if done else -1
    return bool(done) and 0 < first <= 3, "%d blocks, carried light 14 (range 40*1.5=60), timeline %s, first seen t=%s" % (d, p.timeline(), first)


def t_dark_near(c):
    c.far(6)
    p = c.perceive(6, 5)
    done = p.wait_done()
    return bool(done) and done["seen"] >= 3, "6 blocks (sightDark 8), timeline %s, seen %s/5" % (p.timeline(), done and done["seen"])


def t_away(c):
    c.far(10, light=14, fallback=(8,))
    p = c.perceive(10, 6, "away")
    done = p.wait_done()
    return bool(done) and done["seen"] == 0, "lit, facing away at 10: timeline %s (seen %s, sensed %s, heard %s: outside its 70 degree gaze, no noise)" % (p.timeline(), done and done["seen"], done and done["sensed"], done and done["heard"])


def t_sneak(c):
    # Range lit with a torch (14): 40 * (1 + (1.5-1)*min(1, 14/14)) = 60; sneaking x0.5 = 30.
    # At 40 blocks: seen standing (40 <= 60), not seen sneaking (40 > 30).
    dl, d = c.far(40, light=14, fallback=(36, 34, 32))
    p = c.perceive(d, 14)
    p.wait_t(4)
    seen_before = p.count("Seen", 1, 4)
    c.srv.cmd("/backrooms dummy sneak on")
    sneak_t = p.t()
    done = p.wait_done()
    after = p.count("Seen", sneak_t + 2)
    ok = bool(done) and seen_before >= 3 and after == 0 and d > 30
    return ok, "%d blocks, range standing 60, sneaking 30; sneak on at t=%d, timeline %s (seen before %d, after %d)" % (d, sneak_t, p.timeline(), seen_before, after)


def noise_case(c, overrides, expect_heard, label):
    c.far(15)
    p = c.perceive(15, 12, "toward", overrides)
    end = time.time() + 14
    while time.time() < end and p.done() is None:
        c.srv.cmd("/backrooms dummy noise 0.5")
        time.sleep(2)
    done = p.wait_done()
    heard = done["heard"] if done else -1
    ok = bool(done) and (heard >= 3 if expect_heard else heard == 0)
    return ok, "%s, noise 0.5 every 2 s at 15 blocks, timeline %s, heard %s" % (label, p.timeline(), heard)


def t_noise_heard(c):
    return noise_case(c, "", True, "hearing 32 (reach 16 >= 15)")


def t_noise_deaf(c):
    return noise_case(c, "hearing=8", False, "hearing 8 (reach 4 < 15)")


def t_lost(c):
    c.far(20, light=14, fallback=(16,))
    p = c.perceive(20, 24)
    p.wait_t(5)
    first_seen = p.count("Seen", 1, 5)
    c.srv.cmd("/backrooms dummy light 0")
    off_t = p.t()
    done = p.wait_done()
    contacts = p.contacts()
    last_seen = max([t for t, v in contacts.items() if v == "Seen"] or [-1])
    lost = done["lost"] if done else -1
    ok = bool(done) and first_seen >= 3 and last_seen <= off_t + 1 and lost > 0 and 6 <= lost - last_seen <= 10
    return ok, "light out at t=%d, last seen t=%d, lost t=%d (%d s after, expected 8 +-2), timeline %s" % (off_t, last_seen, lost, lost - last_seen, p.timeline())


def t_fear(c):
    c.far(10)
    c.srv.cmd("/backrooms dummy stability 0.3")
    time.sleep(0.5)
    p = c.perceive(10, 5)
    d1 = p.wait_done()
    near = p.count("Sensed")
    by_fear = all("fear" in v[1] for v in p.steps().values() if v[0] == "Sensed")
    ok1 = bool(d1) and near >= 3 and by_fear
    c.srv.cmd("/backrooms perceive stop")
    dl, d = c.far(14)
    c.srv.cmd("/backrooms dummy stability 0.3")
    time.sleep(0.5)
    q = c.perceive(d, 5)
    d2 = q.wait_done()
    far = q.count("Sensed")
    return ok1 and bool(d2) and far == 0 and d > 12, "stability 0.3: at 10 blocks timeline %s (sensed %d, by fear=%s); at %d blocks timeline %s (sensed %d)" % (p.timeline(), near, by_fear, d, q.timeline(), far)


def t_run(c):
    c.far(10)
    c.srv.cmd("/backrooms dummy run on")
    time.sleep(0.5)
    p = c.perceive(10, 5)
    done = p.wait_done()
    steps = p.steps()
    ok = bool(done) and done["heard"] >= 3 and all("run" in v[1] for v in steps.values() if v[0] == "Heard")
    return ok, "running at 10 blocks (heard within 32*0.4=12.8), timeline %s, heard %s" % (p.timeline(), done and done["heard"])


CASES = [("dark-far", t_dark_far), ("lit-far", t_lit_far), ("dark-near", t_dark_near), ("away", t_away), ("sneak", t_sneak),
         ("noise-heard", t_noise_heard), ("noise-deaf", t_noise_deaf), ("lost", t_lost), ("fear", t_fear), ("run", t_run)]


# ---------------------------------------------------------------- P1: the belief-based Menace task (README 5)
# Entities think but do not walk on a headless server, so these cases test decisions (timeouts, noises, sight), not movement.

KIND_RE = re.compile(r"\[backrooms\] (\S+) #(\d+) at [^:]*: (\w+) -> (\w+)")
ENT_LINE_RE = re.compile(r"\[backrooms\] (\S+) #(\d+) at [^:]*: (.*)")
ERR_RE = re.compile(r"\[backrooms\].*(error|exception)|^\s+at \S+\(|Exception:", re.I)


class Enc:
    """One entity put down for a dummy; reads its log lines out of the console."""

    def __init__(self, c, code, kind, dist, light=0, level=LEVEL, min_band=None, ident=True, face=None):
        # (ident=False: the entity logs no "starts:" line (Watcher, Neighborhood Watch); lines() then reads every line of that code)
        self.c, self.srv, self.code = c, c.srv, code
        c.reset()
        c.srv.cmd("/backrooms entitylog on")
        self.band = "?"
        for _ in range(12 if min_band else 1):
            m0 = c.srv.mark()
            k, self.dlight = c.place(None, level)
            if not min_band:
                break
            # (`dummies off` replies with each dummy's band; the director does not direct them)
            m1 = c.srv.mark()
            c.srv.cmd("/backrooms dummies off")
            r = c.srv.wait(lambda l: re.search(r"#\d+ at .*band (\w+)", l), m1, 5)
            self.band = r.group(1) if r else "?"
            if self.band in min_band:
                break
            c.reset()
        else:
            raise RuntimeError("no dummy in a %s band in Level %s (last: %s)" % ("/".join(min_band), level, self.band))
        self.dummy = None
        for l in c.srv.since(m0):
            m = DUMMY_RE.search(l)
            if m:
                self.dummy = (int(m.group(2)), int(m.group(4)))
        if light:
            c.srv.cmd("/backrooms dummy light %d" % light)
        if face:
            # (toward: it stares at whatever asks; away: its back is turned)
            c.srv.cmd("/backrooms dummy face %s" % face)
        time.sleep(1)
        self.mark = c.srv.mark()
        self.reply = None
        for attempt in range(6):
            m = c.srv.mark()
            c.srv.cmd("/backrooms encounter %s %s %d %d %d" % (code, kind, self.dummy[0], self.dummy[1], dist))
            r = c.srv.wait(lambda l: ("put down" in l and l) or ("Found nowhere" in l and l) or ("not loaded" in l and l) or ("No such" in l and l), m, 15)
            if r and "put down" in r:
                self.reply = r
                break
            time.sleep(5)
        else:
            raise RuntimeError("encounter %s %s did not start" % (code, kind))
        self.t0 = time.time()
        self.id = None
        end = time.time() + (10 if ident else 0)
        while time.time() < end and self.id is None:
            for l in c.srv.since(m):
                mm = ENT_LINE_RE.search(l)
                if mm and mm.group(1) == code and "starts:" in mm.group(3):
                    self.id = mm.group(2)
            time.sleep(0.2)
        if self.id is None and ident:
            raise RuntimeError("no 'starts' line for %s (reply: %s)" % (code, self.reply))

    def lines(self):
        return [m.group(3) for m in (ENT_LINE_RE.search(l) for l in self.srv.since(self.mark))
                if m and (m.group(2) == self.id if self.id is not None else m.group(1) == self.code)]

    def kinds(self):
        return [(m.group(3), m.group(4)) for m in (KIND_RE.search(l) for l in self.srv.since(self.mark)) if m and m.group(2) == self.id]

    def changes(self):
        return ", ".join("%s>%s" % k for k in self.kinds())

    def wait_for(self, pred, timeout):
        end = time.time() + timeout
        while time.time() < end:
            if pred():
                return True
            time.sleep(0.3)
        return pred()

    def dist(self):
        """The distance in the first 'Kind, D blocks from' progress line (None before it comes)."""
        for l in self.lines():
            m = re.match(r"\w+, ([\d.]+) blocks from", l)
            if m:
                return float(m.group(1))
        return None

    def has(self, frm, to):
        return (frm, to) in self.kinds()

    def count_lines(self, text):
        return sum(1 for l in self.lines() if text in l)

    def finish(self):
        self.c.reset()
        time.sleep(1)


def started(c, *a, min_dist=0, tries=6, **kw):
    """An Enc whose entity starts at least min_dist blocks off (a short tunnel may put it closer): retried."""
    for _ in range(tries):
        e = Enc(c, *a, **kw)
        e.wait_for(lambda: e.dist() is not None, 8)
        if (e.dist() or 0) >= min_dist:
            return e
        e.finish()
    raise RuntimeError("entity always started nearer than %d blocks" % min_dist)


def t_p1_hunt_to_search(c):
    # (A hunt whose first path fails goes straight back to Stalk: that is a spot with no way through, not belief; retry elsewhere)
    skipped = 0
    for _ in range(8):
        e = Enc(c, "hound", "hunt", 20)
        e.wait_for(lambda: e.dist() is not None, 8)
        time.sleep(5)    # (a path that cannot be found drops the hunt to Stalk within a few seconds)
        if not e.has("Hunt", "Stalk") and (e.dist() or 0) >= 15:
            break
        skipped += 1
        e.finish()
    # A hunt the director sent ("sent hunt") refreshes its belief every 2 s for its first sentHuntSeconds (10), then memory (8 s
    # for the Hound) fades: Hunt -> Search at about 18 to 40 s. Allow 45 s.
    ok1 = e.wait_for(lambda: e.has("Hunt", "Search"), 45)
    t_search = time.time() - e.t0
    ok2 = e.wait_for(lambda: e.has("Search", "Stalk") or e.has("Search", "Leave"), 40)
    ks = e.kinds()
    first = next((i for i, k in enumerate(ks) if k == ("Hunt", "Search")), len(ks))
    rehunt = [k for k in ks[first:] if k[1] == "Hunt"]
    ev = "changes %s; Hunt>Search after %.0f s; %d spots abandoned (too close to be out of sight, or Hunt>Stalk at once: first path failed); started %.0f blocks off" % (e.changes(), t_search, skipped, e.dist() or -1)
    e.finish()
    return ok1 and ok2 and not rehunt and t_search <= 45, ev


def t_p1_stalk_to_investigate(c):
    e = Enc(c, "hound", "stalk", 20)
    time.sleep(3)
    c.srv.cmd("/backrooms dummy noise 0.8")
    ok1 = e.wait_for(lambda: e.has("Stalk", "Investigate"), 8)
    heard = [l for l in e.lines() if l.startswith("hears")]
    ok2 = e.wait_for(lambda: e.has("Investigate", "Stalk") or e.has("Investigate", "Hunt"), 25)
    ev = "changes %s; heard lines %s" % (e.changes(), heard[:2])
    e.finish()
    return ok1 and ok2, ev


def t_p1_sight_hunt(c):
    # Seen with its back turned (isolation round 2: sight alone no longer sets a Hound off; see the iso-hound cases), a
    # lit dummy within 16 blocks is hunted, with the growl first.
    # (The hound is put down at a random angle: the maze may not give a clear line, so try several spots)
    for dist in (14, 14, 14, 10, 10, 8):
        e = Enc(c, "hound", "stalk", dist, light=14, min_band=("Approach", "Threshold"), face="away")
        ok = e.wait_for(lambda: e.has("Stalk", "Hunt"), 10)
        t = time.time() - e.t0
        growl = [l for l in e.lines() if "growl" in l]
        ev = "%d blocks: changes %s after %.1f s; growl lines %s; sees-lines %d" % (dist, e.changes() or "none", t, growl, e.count_lines("sees its target"))
        sees = e.count_lines("sees its target")
        e.finish()
        if sees:
            return ok and bool(growl), ev
    return False, "never saw the lit dummy at 14/10/8 blocks in 6 spots; last: " + ev


def t_p1_glimpse_to_stalk(c):
    # Needs an Approach-or-worse band and a clear line, and a glimpse that stands (40% are crossings, which with no walking
    # go straight to Leave): spots and glimpses are retried until one qualifies.
    notes = []
    for attempt in range(8):
        try:
            e = Enc(c, "hound", "glimpse", 20, light=14, level="6", min_band=("Approach", "Threshold"))
        except RuntimeError as ex:
            notes.append(str(ex))
            continue
        e.wait_for(lambda: e.count_lines("sees its target") or e.has("Glimpse", "Leave"), 6)
        saw, left = e.count_lines("sees its target"), e.has("Glimpse", "Leave")
        t_seen = time.time() - e.t0
        ok = bool(saw) and e.wait_for(lambda: e.has("Glimpse", "Stalk"), 8)
        ev = "attempt %d (band %s): sight at %.1f s, changes %s, stalk after %.1f s, %d lines of 'watched long enough'" % (
            attempt + 1, e.band, t_seen, e.changes() or "none", time.time() - e.t0, e.count_lines("watched them long enough"))
        e.finish()
        if ok:
            return True, ev
        if saw and not left:
            return False, ev
        notes.append(("crossing" if left and not saw else "no sight") + " at %s" % e.band)
    return None, "no standing glimpse with a clear line in an Approach-or-worse band in 8 tries (Level 6): " + ", ".join(notes)


def t_p1_vague_track(c):
    e = started(c, "hound", "stalk", 30, min_dist=20)
    time.sleep(40)
    n = e.count_lines("vague idea")
    rehunt = [k for k in e.kinds() if k[1] == "Hunt"]
    ev = "changes %s; vague-idea lines %d" % (e.changes() or "none", n)
    e.finish()
    return n >= 2 and not rehunt, ev


def t_p1_legacy(c):
    out, ok = [], True
    for code in ("skinstealer", "deathrat"):
        try:
            e = Enc(c, code, "stalk", 8)
        except RuntimeError as ex:
            out.append("%s: %s" % (code, ex))
            ok = False
            continue
        time.sleep(30)
        bad = [k for k in e.kinds() if k[1] in ("Investigate", "Search")]
        # (They have senses profiles since P2, so a "senses:" line is expected; what must stay out is the belief-based kinds)
        out.append("%s: changes %s, %d lines, bad %s" % (code, e.changes() or "none", len(e.lines()), bad))
        ok = ok and not bad
        e.finish()
    return ok, "; ".join(out)


P1_CASES = [("p1-hunt-to-search", t_p1_hunt_to_search), ("p1-stalk-to-investigate", t_p1_stalk_to_investigate),
            ("p1-sight-hunt", t_p1_sight_hunt), ("p1-glimpse-to-stalk", t_p1_glimpse_to_stalk),
            ("p1-vague-track", t_p1_vague_track), ("p1-legacy", t_p1_legacy), ("p1-no-errors", None)]


# ---------------------------------------------------------------- P2/P4 decisions (group p26)

def t_p2_fed_stealer(c):
    e = Enc(c, "skinstealer", "ambient", 6, ident=False)    # (an Ambient stealer logs no "starts:" line)
    time.sleep(1)
    m = c.srv.mark()
    c.srv.cmd("/backrooms feed fed")
    r = c.srv.wait(lambda l: ("Skin-Stealer #" in l and l) or ("No Skin-Stealer" in l and l), m, 8)
    e.mark = c.srv.mark()    # (kind changes from here on)
    time.sleep(20)
    bad = [k for k in e.kinds() if k[1] in ("Stalk", "Hunt")]
    bad += [l for l in e.lines() if "Stalk" in l.split(",")[0] or "Hunt" in l.split(",")[0]]
    m = c.srv.mark()
    c.srv.cmd("/backrooms feed status")
    st = c.srv.wait(lambda l: ("Skin-Stealer #" in l and l) or ("No Skin-Stealer" in l and l), m, 8)
    ev = "feed reply %r; 20 s later status %r; kind changes %s" % (r and r.split("]")[-1].strip()[:80], st and st.split("]")[-1].strip()[:80], e.changes() or "none")
    e.finish()
    return bool(r) and bool(st) and "No Skin-Stealer" not in r + st and ", Ambient" in st and not bad, ev


def t_p4_strider_fear(c):
    # Hunting Hound plus a Strider put down for the same Level 9 dummy: the Strider's Frighten() sends the Hound to Leave.
    notes = []
    for attempt in range(6):
        try:
            e = Enc(c, "hound", "hunt", 10, level="9")
        except RuntimeError as ex:
            notes.append(str(ex))
            continue
        m = c.srv.mark()
        c.srv.cmd("/backrooms encounter neighborhoodwatch hunt %d %d 6" % e.dummy)
        r = c.srv.wait(lambda l: ("put down" in l and l) or ("Found nowhere" in l and l) or ("No such" in l and l), m, 15)
        if not (r and "put down" in r):
            notes.append("strider not put down (%s)" % (r or "no reply")[-60:])
            e.finish()
            continue
        # (The Watch sets the Hound's kind from outside, so the Hound logs no "Hunt -> Leave" itself; what shows is the Watch's
        # "frightens" line and the Hound's own progress lines ("Hunt, N blocks from", every 3 s) stopping: it is running off)
        fright = lambda: [l for l in c.srv.since(m) if re.search(r"neighborhoodwatch #\d+ at [^:]*: frightens hound #%s " % e.id, l)]
        e.wait_for(fright, 12)
        f = fright()
        mark_f = c.srv.mark()
        time.sleep(10)
        after = [l for l in (ENT_LINE_RE.search(x) for x in c.srv.since(mark_f)) if l and l.group(2) == e.id and re.match(r"(Hunt|Stalk), [\d.]+ blocks from", l.group(3))]
        ev = "attempt %d: strider line %s; hound progress lines in the 10 s after: %d; hound kind changes %s" % (
            attempt + 1, f[0].split("]")[-1].strip() if f else "none", len(after), e.changes() or "none")
        e.finish()
        if f and not after:
            return True, ev
        notes.append(ev)
    return False, "no 'frightens hound' followed by a silent Hound in 6 tries: " + " | ".join(notes[-2:])


def t_p4_watcher_fires(c):
    notes = []
    for attempt in range(8):
        try:
            e = Enc(c, "watcher", "hunt", 10, light=14, level="9", ident=False)
        except RuntimeError as ex:
            notes.append(str(ex))
            continue
        e.wait_for(lambda: e.count_lines("fires at") > 0, 30)
        charges, fires = e.count_lines("charges at"), e.count_lines("fires at")
        m = c.srv.mark()
        c.srv.cmd("/backrooms dummies off")
        r = c.srv.wait(lambda l: re.search(r"#\d+ at .*", l) and l, m, 5)
        ev = "attempt %d: %d charge lines, %d fire lines; last watcher lines %s; dummies: %s" % (
            attempt + 1, charges, fires, e.lines()[-2:], (r or "no reply").split("]")[-1].strip()[:120])
        e.finish()
        if charges and fires:
            return True, ev
        notes.append(ev)
    return False, "no charge+fire in 8 spots: " + " | ".join(notes[-2:])


P26_CASES = [("p2-fed-stealer", t_p2_fed_stealer), ("p4-strider-fear", t_p4_strider_fear), ("p4-watcher-fires", t_p4_watcher_fires)]

# ---------------------------------------------------------------- P7 combat (group p7)

def _struck_fights(c, code, kind):
    # Level 0 (the Lobby: nothing hunts there), the dummy carrying a candle (light 7): struck, the creature must go to Hunt
    # and stay there (no stare-down, no Lobby call-off, no Leave), whatever it was doing.
    e = None
    for _ in range(4):
        try:
            e = Enc(c, code, kind, 5, light=7, level="0")
            break
        except RuntimeError:
            c.reset()
    if e is None:
        return None, "no Level 0 spot"
    e.wait_for(lambda: e.dist() is not None, 8)
    time.sleep(2)
    before = e.changes()
    e.mark2 = c.srv.mark()
    m = c.srv.mark()
    c.srv.cmd("/backrooms strike 2")
    r = c.srv.wait(lambda l: ("health" in l.lower() and l) or ("No living" in l and l) or ("No Backrooms" in l and l), m, 8)
    time.sleep(12)
    after = [k for k in e.kinds()]
    hunted = ("Hunt" in [k[1] for k in after])
    bad_lines = [l for l in e.lines() if "stared down" in l or "gives up" in l or "nerve" in l]
    last = after[-1][1] if after else "?"
    ev = "strike reply %r; kinds %s; last %s; stare/give-up lines %d" % ((r or "")[-70:], e.changes() or "none", last, len(bad_lines))
    e.finish()
    return hunted and last == "Hunt" and not bad_lines and bool(r) and "No " not in (r or ""), ev


def t_p7_hound_struck(c):
    # (A spot where the pathfinder finds no way to the dummy drops any hunt to Stalk, struck or not: try three spots)
    for _ in range(3):
        ok, ev = _struck_fights(c, "hound", "stalk")
        if ok:
            break
    return (False, ev) if ok is None else (ok, ev)


def t_p7_bacteria_struck(c):
    ok, ev = _struck_fights(c, "bacteria", "stalk")
    return (False, ev) if ok is None else (ok, ev)


POS_RE = re.compile(r"\[backrooms\] bacteria #(\d+) at (-?\d+),(-?\d+),(-?\d+):")


def _bacteria_pos(c, e):
    """Where the Bacteria last logged itself (x, z), or None."""
    pos = None
    for l in c.srv.since(e.mark):
        m = POS_RE.search(l)
        if m and m.group(1) == e.id:
            pos = (int(m.group(2)), int(m.group(4)))
    return pos


def _bacteria_enc(c, dist, min_dist=0, light=0):
    for _ in range(4):
        try:
            e = Enc(c, "bacteria", "stalk", dist, level="0", light=light)
            e.wait_for(lambda: e.dist() is not None, 8)
            if (e.dist() or 0) >= min_dist:
                return e
            e.finish()
        except RuntimeError:
            c.reset()
    return None


def t_p7_bacteria_cornered(c):
    # The target is 3 blocks off (inside corneredRange 4) and stays there: within a few seconds it lunges, a provoked hunt
    # (no Lobby call-off, no stare-down, no Leave).
    for _ in range(3):
        e = _bacteria_enc(c, 3)
        if e is None:
            return False, "no Level 0 spot"
        if e.dist() is not None and e.dist() > 4.5:
            e.finish()
            continue
        ok = e.wait_for(lambda: e.count_lines("cornered: it lunges") > 0, 8)
        t = time.time() - e.t0
        time.sleep(4)
        last = e.kinds()[-1][1] if e.kinds() else "?"
        bad = [l for l in e.lines() if "gives up" in l or "stared down" in l or "nerve" in l]
        ev = "after %.1f s; kinds %s; last %s; call-off lines %d" % (t, e.changes() or "none", last, len(bad))
        e.finish()
        if ok and e.has("Stalk", "Hunt") and last == "Hunt" and not bad:
            return True, ev
    return False, ev


def t_p7_bacteria_chased(c):
    # Stalking from 10 blocks (a clear line is likelier near); the dummy walks up to about 9 blocks (inside chaseRange 16 and stalkMin-1, outside
    # corneredRange 4) and stays, carrying a torch so that it keeps them in sight: it keeps falling back from them, and after chaseSeconds (10) it howls and turns.
    ev = "no spot"
    for _ in range(14):
        e = _bacteria_enc(c, 10, 8, light=14)
        if e is None:
            return False, "no Level 0 spot"
        d = list(e.dummy)
        for _ in range(9):
            p = _bacteria_pos(c, e)
            if p is None:
                time.sleep(0.5)
                continue
            dx, dz = p[0] - d[0], p[1] - d[1]
            dist = (dx * dx + dz * dz) ** 0.5
            if dist <= 9.5:
                break
            step = max(1, min(3, int(dist - 9)))
            mx, mz = round(dx / dist * step), round(dz / dist * step)
            c.srv.cmd("/backrooms dummy move %d %d" % (mx, mz))
            d[0] += mx
            d[1] += mz
            time.sleep(1)
        # (It sits as put down, facing any way and not turning headless: a spot where it never sees the dummy is no use)
        if not e.wait_for(lambda: e.count_lines("sees its target") > 0, 4):
            ev = "never saw the dummy at %.1f blocks" % dist
            e.finish()
            continue
        ok = e.wait_for(lambda: e.count_lines("chased too long: it turns") > 0 or e.count_lines("cornered") > 0, 22)
        t = time.time() - e.t0
        corner = e.count_lines("cornered") > 0
        time.sleep(2)
        last = e.kinds()[-1][1] if e.kinds() else "?"
        ev = "after %.1f s; dist %.1f; kinds %s; last %s; cornered %s" % (t, dist if p else -1, e.changes() or "none", last, corner)
        e.finish()
        if ok and not corner and e.has("Stalk", "Hunt"):
            return True, ev
    return False, ev


P7_CASES = [("p7-hound-struck", t_p7_hound_struck), ("p7-bacteria-struck", t_p7_bacteria_struck),
            ("p7-bacteria-cornered", t_p7_bacteria_cornered), ("p7-bacteria-chased", t_p7_bacteria_chased)]


# ---------------------------------------------------------------- P7 round 2: isolation, piece A (isolation.md 4.6)
RATE_RE = re.compile(r"ratecheck Level (\d+) (\w+) \(menace ([\d.]+), setting (\w+), [\d.]+ h, \d+ kinds of menacing thing about \(of \d+ allowed\)\): bodies ([\d.]+)/h \(glimpse ([\d.]+), stalk ([\d.]+), hunt ([\d.]+)\), "
                     r"sounds ([\d.]+)/h; body gap mean (\S+) min, min (\S+) min; sound gap mean (\S+) min, min (\S+) min")


def _rate(c, level, band, hours=50, extra=""):
    m = c.srv.mark()
    c.srv.cmd(("/backrooms ratecheck %s %s %s %s" % (level, band, hours, extra)).strip())
    r = c.srv.wait(lambda l: RATE_RE.search(l) or ("ratecheck" in l.lower() and "band" in l.lower() and "Give" in l and l), m, 30)
    if not hasattr(r, "group"):
        raise RuntimeError("no ratecheck reply for Level %s %s (%s)" % (level, band, r))
    g = r.groups()
    return {"bodies": float(g[4]), "glimpse": float(g[5]), "stalk": float(g[6]), "hunt": float(g[7]), "sounds": float(g[8]),
            "gap": g[9], "mingap": g[10], "text": r.group(0)}


def t_iso_rates(c):
    # (level, band, key, lo, hi): measured at the normal setting (dialin.md 3.1; 50 h of ticks), +-35 %: L1 heartland 8.5, L1 threshold 73,
    # L4 approach 20, L0 heartland 7.4, L9 threshold 330, L6 heartland 4.0, L1 heartland sounds 27 (re-measured for the progression round's new normal, Spawns 5.5, 2026-10-25)
    checks = [("1", "heartland", "bodies", 5.5, 11.5), ("1", "threshold", "bodies", 48, 99), ("4", "approach", "bodies", 13, 27),
              ("0", "heartland", "bodies", 4.8, 10), ("9", "threshold", "bodies", 214, 444), ("6", "heartland", "bodies", 2.6, 5.4),
              ("1", "heartland", "sounds", 18, 37)]
    ev, ok, cache = [], True, {}
    for level, band, key, lo, hi in checks:
        r = cache.get((level, band)) or cache.setdefault((level, band), _rate(c, level, band))
        good = lo <= r[key] <= hi
        if level == "0" and band == "heartland":
            good = good and r["stalk"] == 0 and r["hunt"] == 0   # glimpses only
        ok &= good
        ev.append("L%s %s %s %.1f (%s..%s)%s" % (level, band, key, r[key], lo, hi, "" if good else " BAD"))
    # the hard gap: Level 1 heartland bodies are never closer than 25%% of the about 7.1 minute mean
    r = cache[("1", "heartland")]
    try:
        gap_ok = float(r["mingap"]) >= 1.6
    except ValueError:
        gap_ok = False
    ok &= gap_ok
    ev.append("L1 heartland min body gap %s min (>= 1.6)%s" % (r["mingap"], "" if gap_ok else " BAD"))
    return ok, "; ".join(ev)


def t_iso_one_kind(c):
    """The one-kind rule. Deterministic part: the rolls with one menacing entity about put down no body at all, the control does.
    Live part: a stalking Hound about a Level 1 approach dummy for two minutes: no other body is put down for it (compared by entity id)."""
    with_one = _rate(c, "1", "approach", 50, "menacing=1")
    control = _rate(c, "1", "approach", 50)
    det = with_one["bodies"] == 0 and control["bodies"] > 0
    e = started(c, "hound", "stalk", 25, level="1", min_band=("Approach", "Threshold"))
    m = c.srv.mark()
    c.srv.cmd("/backrooms dummies on")
    time.sleep(125)
    others = set()
    for l in c.srv.since(m):
        mm = ENT_LINE_RE.search(l)
        # (only bodies count: ambient wanderers are exempt from the one-kind rule)
        if mm and "starts:" in mm.group(3) and mm.group(2) != e.id and not mm.group(3).strip().endswith("Ambient"):
            others.add("%s#%s" % (mm.group(1), mm.group(2)))
    left = any(k[1] == "Leave" for k in e.kinds())
    c.srv.cmd("/backrooms dummies off")
    e.finish()
    # (a Hound that left lets the director legally put something down: that run proves nothing, so it is not held against the rule)
    live = not others or left
    return det and live, "menacing=1: %.1f bodies/h, control %.1f; live: other bodies %s%s" % (
        with_one["bodies"], control["bodies"], sorted(others) or "none", " (the Hound left)" if left else "")


ISO_CASES = [("iso-rates", t_iso_rates), ("iso-one-kind", t_iso_one_kind)]
# ---- P7 round 2, piece B: the Hound's counters (isolation.md 4.5). The Hound no longer hunts on sight. It closes at a walk and
# charges when the target runs, turns their back, is within 5 blocks, or its nerve breaks under a stare (the entity log names the
# trigger: "hunts: ran" / "back turned" / "nerve" / "too close"). Headless entities never walk, so these are decisions by timeouts.

def _hound_lit(c, dist, face, tries=6):
    """A Hound stalking a lit dummy (in an Approach-or-worse band, so it may hunt) that it sees: retried over spots."""
    for _ in range(tries):
        e = Enc(c, "hound", "stalk", dist, light=14, min_band=("Approach", "Threshold"), face=face)
        if e.wait_for(lambda: e.count_lines("sees its target") > 0, 8):
            return e
        e.finish()
    return None


def _first_line_at(e, text, timeout):
    """The time at which a line containing text first shows, or None."""
    end = time.time() + timeout
    while time.time() < end:
        if e.count_lines(text):
            return time.time()
        time.sleep(0.1)
    return None


def t_iso_hound_nerve(c):
    # A dummy looking straight at it, standing 10 blocks off and steady: it is stared down (no hunt) for its nerve (4 to 8 s),
    # then "hunts: nerve" (the lore: it will not work for long). The nerve is measured from the "stared down" line.
    ev = "no spot"
    for attempt in range(4):
        e = _hound_lit(c, 10, "toward")
        if e is None:
            return False, "no spot with a clear line at 10 blocks"
        t_stare = _first_line_at(e, "stared down", 10)
        if t_stare is None:
            ev = "attempt %d: never stared down; changes %s" % (attempt + 1, e.changes() or "none")
            e.finish()
            continue
        early = e.wait_for(lambda: e.has("Stalk", "Hunt"), 3.2)
        e.wait_for(lambda: e.has("Stalk", "Hunt"), 9)
        t_hunt = time.time() - t_stare
        trig = [l for l in e.lines() if l.startswith("hunts:")]
        ev = "attempt %d: stared down, hunt after %.1f s of it (early %s); triggers %s; changes %s" % (attempt + 1, t_hunt, early, trig, e.changes())
        e.finish()
        if trig and "hunts: nerve" not in trig:
            continue    # (a menace roll got there first: try again)
        return (not early) and bool(trig) and t_hunt <= 10, ev
    return False, ev


def t_iso_hound_back_turned(c):
    # Its target's back is turned, in sight and within 16 blocks: hunted after 2 s of it (and the growl first).
    ev = "no spot"
    for attempt in range(3):
        e = _hound_lit(c, 10, "away")
        if e is None:
            return False, "no spot with a clear line at 10 blocks"
        t_seen = _first_line_at(e, "sees its target", 1) or time.time()
        ok = e.wait_for(lambda: e.has("Stalk", "Hunt"), 10)
        took = time.time() - t_seen
        trig = [l for l in e.lines() if l.startswith("hunts:")]
        ev = "attempt %d: hunt %.1f s after the first sight; triggers %s; growl lines %d; changes %s" % (attempt + 1, took, trig, e.count_lines("growls"), e.changes())
        e.finish()
        if ok and trig == ["hunts: back turned"] and took <= 5:
            return True, ev
    return False, ev


def t_iso_hound_runner(c):
    # A dummy that runs, looking straight at the Hound (running beats the stare): hunted, "hunts: ran".
    ev = "no spot"
    for attempt in range(3):
        e = _hound_lit(c, 10, "toward")
        if e is None:
            return False, "no spot with a clear line at 10 blocks"
        c.srv.cmd("/backrooms dummy run on")
        t_run = time.time()
        ok = e.wait_for(lambda: e.has("Stalk", "Hunt"), 10)
        took = time.time() - t_run
        trig = [l for l in e.lines() if l.startswith("hunts:")]
        ev = "attempt %d: hunt %.1f s after it ran; triggers %s; changes %s" % (attempt + 1, took, trig, e.changes())
        e.finish()
        if ok and trig == ["hunts: ran"]:
            return True, ev
    return False, ev


def t_iso_hound_gives_up(c):
    # A Hound sent after a dummy that is dark and out of its line (20 blocks): its belief fades, it searches, and then it leaves.
    # It must not go back to following (Search > Stalk) once it has lost them, nor hunt again.
    ev = "no run"
    for attempt in range(4):
        e = Enc(c, "hound", "hunt", 20)
        e.wait_for(lambda: e.dist() is not None, 8)
        ok1 = e.wait_for(lambda: e.has("Hunt", "Search"), 50)
        t_search = time.time() - e.t0
        ok2 = e.wait_for(lambda: e.has("Search", "Leave"), 40)
        ks = e.kinds()
        first = next((i for i, k in enumerate(ks) if k == ("Hunt", "Search")), len(ks))
        back = [k for k in ks[first:] if k in (("Search", "Stalk"), ("Search", "Hunt"), ("Leave", "Stalk"), ("Leave", "Hunt"))]
        ev = "attempt %d: Hunt>Search after %.0f s, Search>Leave %s; changes %s; lost-lines %d, no-way lines %d, search lines %d, gives up lines %d" % (
            attempt + 1, t_search, ok2, e.changes(), e.count_lines("has lost them"), e.count_lines("no way through"), e.count_lines("searches"), e.count_lines("gives up the search"))
        e.finish()
        if ok1 and ok2 and not back:
            return True, ev
    return False, ev


ISO_HOUND_CASES = [("iso-hound-nerve", t_iso_hound_nerve), ("iso-hound-back-turned", t_iso_hound_back_turned),
                   ("iso-hound-runner", t_iso_hound_runner), ("iso-hound-gives-up", t_iso_hound_gives_up)]


# ---- P7 play-test: the Level 1 Flickering. Nothing is put down for the first 8 to 15 s of the dark; the pack is put down at least
# 20 blocks off; and the hunt lasts the Flickering (no call-off for lack of blood, no drop to Stalk, no Leave) until the lights return.

HOUND_AT_RE = re.compile(r"\[backrooms\] hound #(\d+) at (-?\d+),(-?\d+),(-?\d+): starts:")
FLICKER_DELAY_RE = re.compile(r"flicker: the Hounds come in ([\d.]+) s")
CUE_RE = re.compile(r"\[backrooms\] sound (\S+) for")
BAND_RE = re.compile(r"hound x\d+ \(\w+\) for .*band (\w+)")


def t_p7_flicker(c):
    ev = "no spot"
    for attempt in range(3):
        c.reset()
        c.srv.cmd("/backrooms entitylog on")
        m0 = c.srv.mark()
        try:
            c.place(level="1")
        except RuntimeError as e:
            return False, str(e)
        dummy = None
        for l in c.srv.since(m0):
            mm = DUMMY_RE.search(l)
            if mm:
                dummy = (int(mm.group(2)), int(mm.group(4)))
        time.sleep(1)
        m = c.srv.mark()
        t0 = time.time()
        c.srv.cmd("/backrooms flicker")
        # Another menacing entity about (a Wretch stalking): the Hounds must come all the same
        time.sleep(0.5)
        if dummy:
            c.srv.cmd("/backrooms encounter wretch stalk %d %d" % (dummy[0], dummy[1]))
        r = c.srv.wait(lambda l: ("lights fail" in l and l) or ("Needs a player" in l and l) or ("Hounds are coming" in l and l), m, 10)
        if not r or "lights fail" not in r:
            ev = "attempt %d: flicker reply: %s" % (attempt + 1, r)
            continue
        first = None
        cue_at = None
        end = time.time() + 45
        while time.time() < end and first is None:
            if cue_at is None and any(CUE_RE.search(l) for l in c.srv.since(m)):
                cue_at = time.time() - t0
            for l in c.srv.since(m):
                mm = HOUND_AT_RE.search(l)
                if mm:
                    first = (time.time() - t0, int(mm.group(2)), int(mm.group(4)), mm.group(1))
                    break
            time.sleep(0.2)
        cues = [mm.group(1) for mm in (CUE_RE.search(l) for l in c.srv.since(m)) if mm]
        band = next((mm.group(1) for mm in (BAND_RE.search(l) for l in c.srv.since(m)) if mm), "?")
        delay = next((float(mm.group(1)) for mm in (FLICKER_DELAY_RE.search(l) for l in c.srv.since(m)) if mm), None)
        if first is None:
            ev = "attempt %d: no Hound put down in 45 s (delay %s)" % (attempt + 1, delay)
            continue
        off = ((first[1] - dummy[0]) ** 2 + (first[2] - dummy[1]) ** 2) ** 0.5
        ev = "attempt %d: delay %.1f s, first Hound at %.1f s, %.0f blocks off" % (attempt + 1, delay or -1, first[0], off)
        cue_ok = len(cues) >= 1 and all("wolf" in x for x in cues) and cue_at is not None and cue_at <= 4.8
        ev += "; first cue at %s s, cues %s; band %s" % (cue_at, cues, band)
        late_enough = first[0] >= 4.5 and delay is not None and 5 <= delay <= 10.1 and cue_ok
        # Run the dummy away: while the lights are out it must not be called off for lack of blood nor leave, and ends up hunting or searching
        c.srv.cmd("/backrooms dummy run on")
        c.srv.cmd("/backrooms dummy move 30 0")
        time.sleep(50)
        kinds = [(mm.group(3), mm.group(4)) for mm in (KIND_RE.search(l) for l in c.srv.since(m)) if mm and mm.group(2) == first[3]]
        lines = [mm.group(3) for mm in (ENT_LINE_RE.search(l) for l in c.srv.since(m)) if mm and mm.group(2) == first[3]]
        called_off = sum(1 for l in lines if "gives up the hunt" in l)
        # (A hunt whose first path fails falls back to Stalk for a few seconds, as any hunt does; what matters is that it is hunting or searching at the end; no change at all means it stayed in its first Hunt)
        bad = [k for k in kinds if k[1] == "Leave"] + ([] if not kinds or kinds[-1][1] in ("Hunt", "Search") else [("last", kinds[-1][1])])
        ev += "; in the dark: %s, call-offs %d, notion lines %d" % (kinds, called_off, sum(1 for l in lines if "notion" in l))
        if not late_enough or off < 20 or called_off or bad:
            return False, ev
        # (The lights return: the calendar is moved on past the Flickering. The behaviour sends the Hound away without a log line of its
        # own, so it has left when it logs nothing more)
        c.srv.cmd("/time add 2")
        time.sleep(12)
        m2 = c.srv.mark()
        time.sleep(8)
        gone = not [l for l in c.srv.since(m2) if "hound #%s " % first[3] in l]
        ev += "; left when the lights returned: %s (silent for 8 s after the calendar moved on)" % gone
        return gone, ev
    return False, ev


FLICKER_CASES = [("p7-flicker", t_p7_flicker)]



# ---------------------------------------------------------------- P7 round 2: the Skin-Stealer (group p7-stealer)
STEALER_RE = re.compile(r"Skin-Stealer #(\d+): (fed|hungry).*?, (\w+), at (-?[\d.]+),(-?[\d.]+),(-?[\d.]+)")


def _stealer_status(c):
    m = c.srv.mark()
    c.srv.cmd("/backrooms feed status")
    r = c.srv.wait(lambda l: STEALER_RE.search(l) or ("No Skin-Stealer" in l and l), m, 8)
    return r if hasattr(r, "group") else None


def _move_dummy_to(c, e, want, at):
    """Moves the dummy (tracked in e.dummy) to `want` blocks from the point `at` (x, z), along the line from where it stands."""
    dx, dz = at[0] - e.dummy[0], at[1] - e.dummy[1]
    dist = (dx * dx + dz * dz) ** 0.5 or 1
    mx, mz = round(dx * (dist - want) / dist), round(dz * (dist - want) / dist)
    c.srv.cmd("/backrooms dummy move %d %d" % (mx, mz))
    e.dummy = (e.dummy[0] + mx, e.dummy[1] + mz)
    time.sleep(1.5)


def t_p7s_fed_guard(c):
    # A fed stealer 12+ blocks off stays Ambient; the dummy comes within about 3 blocks and it turns on them (Ambient > Hunt); the
    # dummy goes 20 blocks off and it is calm again (Hunt > Ambient), without Stalk, Leave or a hunt from afar.
    ev = "no spot"
    for _ in range(6):
        try:
            e = Enc(c, "skinstealer", "ambient", 14, level="1", min_band=("Heartland", "Approach", "Threshold"), ident=False)
        except RuntimeError as ex:
            return False, str(ex)
        time.sleep(1)
        m = c.srv.mark()
        c.srv.cmd("/backrooms feed fed")
        st = c.srv.wait(lambda l: STEALER_RE.search(l) or ("No Skin-Stealer" in l and l), m, 8)
        e.mark = c.srv.mark()
        if not hasattr(st, "group"):
            e.finish()
            continue
        e.id = st.group(1)
        pos = (float(st.group(4)), float(st.group(6)))
        far = ((pos[0] - e.dummy[0]) ** 2 + (pos[1] - e.dummy[1]) ** 2) ** 0.5
        if far < 8:
            e.finish()
            continue
        time.sleep(8)
        quiet = not [k for k in e.kinds()] and not [l for l in e.lines() if l.startswith(("Stalk", "Hunt"))]
        _move_dummy_to(c, e, 3, pos)
        turned = e.wait_for(lambda: e.has("Ambient", "Hunt"), 8)
        t_turn = time.time() - e.t0
        time.sleep(2)
        _move_dummy_to(c, e, 22, pos)
        calm = e.wait_for(lambda: e.has("Hunt", "Ambient"), 14)
        bad = [k for k in e.kinds() if k[1] in ("Stalk", "Leave", "Search", "Glimpse")]
        ev = "band %s; %.0f blocks off at first, quiet 8 s: %s; turned on them: %s; calm after backing off: %s; kinds %s" % (
            e.band, far, quiet, turned, calm, e.changes() or "none")
        e.finish()
        if quiet and turned and calm and not bad:
            return True, ev
    return False, ev


def t_p7s_hungry_comes(c):
    # A hungry stealer stalks a dummy in the Approach or Threshold band: it must come for them (Stalk > Hunt) without leaving.
    ev = "no spot"
    for _ in range(6):
        try:
            e = Enc(c, "skinstealer", "stalk", 14, level="1", min_band=("Approach", "Threshold"))
        except RuntimeError as ex:
            return False, str(ex)
        e.wait_for(lambda: e.dist() is not None, 8)
        c.srv.cmd("/backrooms feed hungry")
        limit = 22 if e.band == "Threshold" else 40
        # (A spot where it never sees the dummy proves nothing)
        if not e.wait_for(lambda: e.count_lines("sees its target") > 0, 6):
            ev = "never saw the dummy"
            e.finish()
            continue
        t0 = time.time()
        came = e.wait_for(lambda: e.has("Stalk", "Hunt") or e.has("Glimpse", "Hunt"), limit)
        took = time.time() - t0
        left = [k for k in e.kinds() if k[1] == "Leave"]
        ev = "band %s; came for them: %s after %.0f s (limit %d); Leave %s; kinds %s; escalation lines %d" % (
            e.band, came, took, limit, bool(left), e.changes() or "none", e.count_lines("stalked long enough"))
        e.finish()
        if came and not left:
            return True, ev
    return False, ev


def t_p7s_hungry_glimpse(c):
    # A hungry glimpse that has watched them for a while follows (Glimpse > Stalk) rather than walking off, from the Approach band out.
    ev = "no spot"
    for _ in range(6):
        try:
            e = Enc(c, "skinstealer", "glimpse", 18, light=14, level="1", min_band=("Approach", "Threshold"))
        except RuntimeError as ex:
            return False, str(ex)
        # (A glimpse that stands and sees: crossings go straight to Leave with no walking, and some are put down fed, so docile)
        if not e.wait_for(lambda: e.count_lines("sees its target") > 0 or e.has("Glimpse", "Leave") or e.has("Ambient", "Hunt"), 6)                 or e.count_lines("sees its target") == 0:
            ev = "no standing glimpse with a clear line (%s)" % (e.changes() or "none")
            e.finish()
            continue
        turned = e.wait_for(lambda: e.has("Glimpse", "Stalk") or e.has("Glimpse", "Hunt"), 12)
        ev = "band %s; glimpse turned to stalk: %s; kinds %s" % (e.band, turned, e.changes() or "none")
        e.finish()
        if turned:
            return True, ev
    return False, ev


STEALER_CASES = [("p7-stealer-fed", t_p7s_fed_guard), ("p7-stealer-hungry", t_p7s_hungry_comes), ("p7-stealer-glimpse", t_p7s_hungry_glimpse)]

# ---- P7 round 5, piece B: the felt rate (dialin.md 3.9). The director's placement dry-run in every busy level: a roll that finds no
# spot is silence, so stalk-or-hunt must be placeable at least a quarter of the time wherever the player stands in the approach band.
FELT_LEVELS = ["1", "2", "3", "4", "5", "8", "9", "94"]
FELT_TABLE = []


def _felt_band(c):
    m1 = c.srv.mark()
    c.srv.cmd("/backrooms dummies off")
    r = c.srv.wait(lambda l: re.search(r"#\d+ at .*band (\w+)", l), m1, 5)
    return r.group(1) if r else "?"


def _felt_place(c, level):
    """A dummy in the approach band if the level has one (else threshold, else the busiest band it gets); a dummy that lands in a
    quieter band is walked outward (`dummy move`) a few times."""
    best = None
    for n in range(12):
        c.reset()
        c.place(None, "nest" if level == "8" else level)
        band = _felt_band(c)
        for dx, dz in ((120, 0), (0, 120), (-240, 0), (0, -240), (240, 240)):
            if band in ("Approach", "Threshold"):
                break
            c.srv.cmd("/backrooms dummy move %d %d" % (dx, dz))
            time.sleep(2)
            band = _felt_band(c)
        if band == "Approach":
            return band
        if band == "Threshold" and n >= 4:
            return band
        if best is None or band in ("Threshold", "Approach") or (band == "Heartland" and best not in ("Threshold", "Approach")):
            if band != "Safe":
                best = band
    return best


def t_felt_rates(c):
    ev, ok = [], True
    FELT_TABLE.clear()
    for level in FELT_LEVELS:
        night = level == "94"
        if night:
            c.srv.cmd("/time set 23")
            time.sleep(2)
        try:
            band = _felt_place(c, level)
            if band is None or band == "?":
                ok = False
                ev.append("L%s: no dummy outside the Safe band" % level)
                continue
            m = c.srv.mark()
            c.srv.cmd("/backrooms feltrate here %s 40" % band.lower())
            r = c.srv.wait(lambda l: "stalk-or-hunt" in l and "felt bodies" in l, m, 90)
            if not r:
                ok = False
                ev.append("L%s: no feltrate reply" % level)
                continue
            reply = "\n".join(c.srv.since(m))
            mm = re.search(r"stalk-or-hunt (\d+)%.*?(\d+) no floor/room, (\d+) in sight.*?felt bodies ([\d.]+)/h", reply, re.S)
            if not mm:
                ok = False
                ev.append("L%s: unreadable reply %r" % (level, reply[-200:]))
                continue
            kinds = {k: int(v) for k, v in re.findall(r"(Glimpse|Stalk|Hunt): \d+ kinds on the roster, placed (\d+)%", reply)}
            sh = int(mm.group(1))
            good = sh >= 25
            ok &= good
            FELT_TABLE.append((level, band, kinds, sh, int(mm.group(2)), int(mm.group(3)), float(mm.group(4))))
            ev.append("L%s %s: glimpse %s%% stalk %s%% hunt %s%%, stalk-or-hunt %d%%%s, refused looks %s no floor %s in sight, felt %.1f/h" % (
                level, band, kinds.get("Glimpse", "-"), kinds.get("Stalk", "-"), kinds.get("Hunt", "-"), sh, "" if good else " BAD",
                mm.group(2), mm.group(3), float(mm.group(4))))
        finally:
            if night:
                c.srv.cmd("/time set 12")
                time.sleep(1)
    c.reset()
    return ok, "\n  ".join([""] + ev)


FELT_CASES = [("felt-rates", t_felt_rates)]

# ---- Needs, piece A (docs/design/needs/README.md, section 12): thirst and fatigue. The pure-math self-test, a clean boot with the
# player patch, and the director's multiplier through the rate check (1 at 0 awake hours, so iso-rates is untouched).
NEEDS_TEST_RE = re.compile(r"needstest: (\d+) checks, (\d+) failed")


def t_needs_selftest(c):
    m = c.srv.mark()
    c.srv.cmd("/backrooms needstest")
    r = c.srv.wait(lambda l: NEEDS_TEST_RE.search(l), m, 20)
    if not r:
        return False, "no needstest summary"
    time.sleep(0.5)
    fails = [l.strip() for l in c.srv.since(m) if re.search(r"\bFAIL ", l)]
    checks, failed = int(r.group(1)), int(r.group(2))
    return failed == 0 and not fails and checks >= 40, "%d checks, %d failed%s" % (checks, failed, "".join("\n  " + f[:200] for f in fails[:8]))


def t_needs_boot(c):
    """The server booted with the needs' player patch and behaviours: nothing in the log about them failing."""
    bad = [l for l in c.srv.since(0)[:getattr(c.srv, "boot_end", 10 ** 9)] if re.search(r"needs|backrooms-thirst|backrooms-fatigue|player-needs", l, re.I)
           and re.search(r"error|exception|fail|not found|unknown|could not", l, re.I) and not l.startswith(">>>") and "needstest" not in l]
    return not bad, "%d needs error lines in the boot log%s" % (len(bad), "".join("\n  " + b[:200] for b in bad[:5]))


def t_needs_rates(c):
    """`ratecheck awake=<h>`: the multiplier is 1 at 0 awake hours and about 2.9 at 70 (Level 1 heartland, 400 simulated hours)."""
    base = _rate(c, "1", "heartland", 400, "awake=0")
    tired = _rate(c, "1", "heartland", 400, "awake=70")
    ratio = tired["bodies"] / base["bodies"] if base["bodies"] > 0 else 0
    ok = 2.3 <= ratio <= 3.6
    return ok, "Level 1 heartland bodies/h: awake 0 %.2f, awake 70 %.2f, ratio %.2f (want about 2.9)" % (base["bodies"], tired["bodies"], ratio)


NEEDS_CASES = [("needs-boot", t_needs_boot), ("needs-selftest", t_needs_selftest), ("needs-rates", t_needs_rates)]

def _pathtest(c, args, tries=12):
    """`/backrooms pathtest <args>`: the report line, retrying while the chunks load."""
    for _ in range(tries):
        m = c.srv.mark()
        c.srv.cmd("/backrooms pathtest " + args)
        r = c.srv.wait(lambda l: re.search(r"(?:FOUND|NO PATH).*|The chunks are loading", l), m, 15)
        if r and "chunks are loading" not in r.group(0):
            return r.group(0)
        time.sleep(5)
    return None


def t_path_cubicle_partition(c):
    """Level 4's cubicles (seed 12345, around 514670,511988): a Duller from one side of a back partition to the other must be sent
    round it (13+ steps for 4 blocks), not over it (3 steps: the game's step test let a 1.5 high partition through)."""
    line = _pathtest(c, "duller 514670 511990 514670 511986")
    if line is None:
        return False, "no pathtest report"
    steps = re.search(r"(\d+) steps", line)
    return line.startswith("FOUND") and steps is not None and int(steps.group(1)) >= 10, line[:200]


def t_path_party_door(c):
    """Level Fun: a Partygoer standing at its party (a guest's stand round the head table) must have a path out through the room's
    doorway to the corridor (the doorway is 2 blocks high: a 2.2 high hitbox was planned nowhere). `/backrooms partypath` tries every
    guest stand against every doorway of the party rooms near a straw dummy put down in Level Fun."""
    last = "no party room with guests found"
    for key in range(1, 9):
        try:
            c.place(key, "fun")
        except RuntimeError:
            continue
        dummy = None
        for l in reversed(c.srv.since(0)):
            dummy = DUMMY_RE.search(l)
            if dummy:
                break
        if not dummy:
            continue
        x, z = int(dummy.group(2)), int(dummy.group(4))
        for _ in range(8):
            m = c.srv.mark()
            c.srv.cmd("/backrooms partypath partygoer %d %d 48" % (x, z))
            r = c.srv.wait(lambda l: re.search(r"partypath: (\d+) rooms, (\d+) doors, (\d+) guest-door pairs, (\d+) found|The chunks are loading|Error", l), m, 30)
            if r and r.group(1) is not None:
                rooms, doors, tried, found = (int(r.group(i)) for i in range(1, 5))
                lines = [l.strip() for l in c.srv.since(m) if "room " in l and "spot " in l]
                last = "dummy key %d at %d,%d: %d rooms, %d doors, %d pairs, %d found; %s" % (key, x, z, rooms, doors, tried, found, " | ".join(l[-90:] for l in lines[:3]))
                if tried >= 2:
                    return found == tried, last
                break
            time.sleep(4)
    return False, last


PATH_CASES = [("path-cubicle-partition", t_path_cubicle_partition), ("path-party-door", t_path_party_door)]

# ---------------------------------------------------------------- progression round, piece B: lethality and speed (plan.md 3.5)
# `/backrooms armourtest <entity> <level> [set]` re-runs vanilla's armour rules on the real items (a straw dummy cannot wear any) and logs
# one line per set; the speed floor is read off the entity log's "pace:" line (headless entities never walk).
ARM_RE = re.compile(r"armourtest (\S+) L(\S+) (\S+): head ([\d.]+) body ([\d.]+) legs ([\d.]+); mean ([\d.]+); blows to kill (\S+) \((\d+) to (\S+)\)")
ARM_SETS = ("none", "jerkin-leather", "sewn-leather", "lamellar-copper", "lamellar-tinbronze", "chain-copper", "chain-tinbronze",
            "plate-copper", "plate-tinbronze", "chain-iron", "plate-iron")
ARM_LEVELS = ("1", "3", "5", "8", "9", "11")


def _armour_table(c, code):
    """{(level, set): dict(mean=, blows=, fewest=, most=)} for one entity, by one armourtest command per level."""
    table = {}
    for level in ARM_LEVELS:
        m = c.srv.mark()
        c.srv.cmd("/backrooms armourtest %s %s" % (code, level))
        end = time.time() + 15
        while time.time() < end and sum(1 for l in c.srv.since(m) if ARM_RE.search(l)) < len(ARM_SETS):
            time.sleep(0.2)
        for l in c.srv.since(m):
            g = ARM_RE.search(l)
            if g:
                blows = float(g.group(8)) if g.group(8) != "never" else 99.0
                table[(g.group(2), g.group(3))] = dict(mean=float(g.group(7)), blows=blows, fewest=int(g.group(9)),
                                                      most=99 if g.group(10) == "never" else int(g.group(10)),
                                                      zones=(float(g.group(4)), float(g.group(5)), float(g.group(6))))
    return table


def t_prog_armour(c):
    ev, ok = [], True
    for code in ("smiler", "hound"):
        t = _armour_table(c, code)
        if len(t) < len(ARM_LEVELS) * len(ARM_SETS):
            return False, "armourtest %s gave %d of %d lines" % (code, len(t), len(ARM_LEVELS) * len(ARM_SETS))
        for level in ARM_LEVELS:
            ev.append("%s L%s: %s" % (code, level, " | ".join("%s %.1f/%s" % (s.replace("lamellar", "lam").replace("-tinbronze", "-sn").replace("-copper", "-cu"),
                                                                             t[(level, s)]["mean"], "%.1f" % t[(level, s)]["blows"]) for s in ARM_SETS)))
        none3, none8 = t[("3", "none")], t[("8", "none")]
        checks = [
            ("unarmoured 2-3 blows at L3", 2 <= math.ceil(none3["blows"]) <= 3),
            ("unarmoured 1-2 blows at L8", 1 <= math.ceil(none8["blows"]) <= 2),
            ("sewn leather at most 0.6 x the unarmoured blow at L3", t[("3", "sewn-leather")]["mean"] <= 0.6 * none3["mean"]),
            ("copper lamellar stands two blows at L8 (even the worst piece)", t[("8", "lamellar-copper")]["fewest"] >= 3),
            ("bronze lamellar stands two blows at L8 (even the worst piece)", t[("8", "lamellar-tinbronze")]["fewest"] >= 3),
            ("iron plate stands two blows at L9 (even the worst piece)", t[("9", "plate-iron")]["fewest"] >= 3),
            ("more depth never hits softer (unarmoured)", all(t[(a, "none")]["mean"] <= t[(b, "none")]["mean"] + 1e-6 for a, b in zip(ARM_LEVELS, ARM_LEVELS[1:]))),
            ("better armour never hurts more (L8)", t[("8", "plate-iron")]["mean"] <= t[("8", "lamellar-tinbronze")]["mean"] <= t[("8", "none")]["mean"]),
        ]
        for what, good in checks:
            ok &= good
            if not good:
                ev.append("%s: BAD %s" % (code, what))
    return ok, "; ".join(ev)


PACE_RE = re.compile(r"pace: danger ([\d.]+), run ([\d.]+), walk ([\d.]+), hit ([\d.]+) tier (\d+)")
SPRINT = 0.05


def _pace(c, code, level):
    for _ in range(4):
        try:
            e = Enc(c, code, "hunt", 12, level=level)
        except RuntimeError:
            c.reset()
            continue
        e.wait_for(lambda: any(PACE_RE.search(l) for l in e.lines()), 8)
        found = [PACE_RE.search(l) for l in e.lines()]
        e.finish()
        found = [f for f in found if f]
        if found:
            g = found[0]
            return dict(danger=float(g.group(1)), run=float(g.group(2)), walk=float(g.group(3)), hit=float(g.group(4)), tier=int(g.group(5)))
    return None


def t_prog_speed(c):
    # (code, level, least run speed or None, most run speed or None): from danger .36 a hunter runs at least 1.15 sprints, 1.4 from Level 9;
    # the lore-slow (Wretch, Duller) keep their own pace, so a Wretch stays under the floor
    # (the entity's own danger is the one of the level it was put down in, which a dummy near a border may not share: the floor is computed from it)
    def floor(d):
        return SPRINT * (1.15 + 0.25 * min(1.0, (d - 0.36) / 0.46)) if d >= 0.36 else 0.0
    plan = [("smiler", "3", True), ("skinstealer", "3", True), ("hound", "3", True), ("deathrat", "3", True),
            ("smiler", "9", True), ("skinstealer", "9", True), ("smiler", "1", False), ("wretch", "3", False)]
    ev, ok = [], True
    for code, level, floored in plan:
        p = _pace(c, code, level)
        if p is None:
            ev.append("%s L%s: no pace line" % (code, level))
            ok = False
            continue
        f = floor(p["danger"])
        # (the pace line prints four decimals)
        good = p["run"] >= f - 0.00006 if floored else p["run"] < max(f, SPRINT * 1.15) - 0.00006 or f == 0
        good = good and (not floored or f > 0)
        ok &= good
        ev.append("%s L%s danger %.2f run %.4f (%.2f sprints; floor %.4f), hit %.1f%s" % (code, level, p["danger"], p["run"], p["run"] / SPRINT, f, p["hit"], "" if good else " BAD"))
    return ok, "; ".join(ev)


PROG_CASES = [("prog-armour", t_prog_armour), ("prog-speed", t_prog_speed)]



# ---------------------------------------------------------------- progression pressure, piece A (reality): the zero blackout
ZERO_RE = re.compile(r"zero: dummy #(\d+) lost their grip in Level (\S+) and came to in Level (\S+)")


def t_prog_zero(c):
    """A dummy at stability 0 in Level 3 is sent the level's worst hunter at once and, after 60 s at zero, is moved to a random
    spot in Level 2 (the zero line says where it came to). A dummy at zero in Level 0 is left alone."""
    c.reset()
    c.place(level="3")
    m = c.srv.mark()
    c.srv.cmd("/backrooms dummy stability 0")
    sent = c.srv.wait(lambda l: re.search(r"zero: (sending \S+ for \S+|Level \S+ has no hunter)", l), m, 15)
    moved = c.srv.wait(lambda l: ZERO_RE.search(l), m, 110)
    c.srv.cmd("/backrooms dummy stability 0.5")
    ok = bool(sent) and bool(moved) and moved.group(2) == "3" and moved.group(3) == "2"
    ev = "hunter: %s; moved: %s" % (sent.group(0) if sent else None, moved.group(0) if moved else None)
    c.reset()
    return ok, ev


def t_prog_zero_safe(c):
    """Zero in Level 0 (a safe place): nothing is sent and nobody is moved in 70 s."""
    c.reset()
    c.place(level="0")
    m = c.srv.mark()
    c.srv.cmd("/backrooms dummy stability 0")
    hit = c.srv.wait(lambda l: re.search(r"zero: ", l) and "[backrooms]" in l, m, 70)
    c.srv.cmd("/backrooms dummy stability 1")
    c.reset()
    return hit is None, "no zero line in 70 s" if hit is None else "unexpected: " + hit


PROG_CASES = PROG_CASES + [("prog-zero", t_prog_zero), ("prog-zero-safe", t_prog_zero_safe)]



# ---------------------------------------------------------------- simulated players (tools/aitest/walk.py, src/Entities/MenaceSystem.Walker.cs)
WALKER_STATUS_RE = re.compile(r"status: Level (\S+), phase (\w+), at (-?\d+) (-?\d+) (-?\d+), band (\w+), hp ([\d.]+)/15, hunger (\d+)%.*?encounters seen (\d+) fled (\d+) hid (\d+) died (\d+); blocks walked (\d+), caches (\d+), laps (\d+), gates (\d+), stuck (\d+)")


def _walker_status(c):
    """`walker status` as a dict, or None."""
    m = c.srv.mark()
    c.srv.cmd("/backrooms walker status")
    r = c.srv.wait(lambda l: WALKER_STATUS_RE.search(l), m, 15)
    if not r:
        return None
    g = r.groups()
    return dict(level=g[0], phase=g[1], x=int(g[2]), y=int(g[3]), z=int(g[4]), band=g[5], hp=float(g[6]), hunger=int(g[7]), seen=int(g[8]), fled=int(g[9]),
                hid=int(g[10]), died=int(g[11]), blocks=int(g[12]), caches=int(g[13]), laps=int(g[14]), gates=int(g[15]), stuck=int(g[16]))


def _walker_start(c, level, armour, minutes):
    c.reset()
    c.srv.cmd("/backrooms dummies off")
    time.sleep(1)
    m = c.srv.mark()
    c.srv.cmd("/backrooms telemetry on")
    time.sleep(1)
    c.srv.cmd("/backrooms walker start %s %s 7 %d" % (level, armour, minutes))
    return m, c.srv.wait(lambda l: "walker placed" in l and l, m, 240)


def _walker_stop(c):
    c.srv.cmd("/backrooms walker stop")
    time.sleep(3)
    c.srv.cmd("/backrooms dummies off")
    time.sleep(1)


def t_walker_smoke(c):
    """A walker in Level 1 for 5 minutes: placed, walks (a few hundred blocks), no errors."""
    m, placed = _walker_start(c, "1", "leather", 5)
    if not placed:
        _walker_stop(c)
        return False, "the walker was never placed"
    try:
        c.srv.wait(lambda l: re.search(r"walker final \(time\)", l), m, 6 * 60 + 60)
    finally:
        st = None
        if not any("walker final" in l for l in c.srv.since(m)):
            st = _walker_status(c)
            _walker_stop(c)
    final = [WALKER_STATUS_RE.search(l) for l in c.srv.since(m) if "walker final" in l]
    final = [f for f in final if f]
    blocks = int(final[-1].group(13)) if final else (st["blocks"] if st else 0)
    bad = [l for l in c.srv.since(m) if ERR_RE.search(l)]
    ok = blocks >= 150 and not bad
    return ok, "5 min in Level 1: walked %d blocks (wanted 150 or more), %d error lines%s" % (blocks, len(bad), "".join(chr(10) + "  " + b[:200] for b in bad[:3]))


def t_walker_struck(c):
    """A blow through the entities' strike path (Strike.Hit) lands on the walker: bare, it takes it whole; in iron it takes less."""
    c.srv.cmd("/backrooms entitylog on")
    time.sleep(1)
    out = []
    ok = True
    for armour, scale in (("none", 1.0), ("iron", 1.0)):
        m, placed = _walker_start(c, "3", armour, 3)
        if not placed:
            _walker_stop(c)
            return False, "the walker was never placed"
        try:
            takes = []
            for _ in range(9):
                m2 = c.srv.mark()
                c.srv.cmd("/backrooms walker hit 1.5 2")
                r = c.srv.wait(lambda l: re.search(r"walker takes ([\d.]+) from (\w+) \(raw ([\d.]+)\)", l), m2, 10)
                if r:
                    takes.append((float(r.group(1)), float(r.group(3))))
                time.sleep(0.3)
        finally:
            _walker_stop(c)
        taken, raw = sum(t for t, _ in takes), sum(r for _, r in takes)
        out.append("%s: %d blows, %.1f of %.1f" % (armour, len(takes), taken, raw))
        if len(takes) < 8:
            ok = False
        elif armour == "none" and abs(taken - raw) > 0.1:
            ok = False
        elif armour == "iron" and taken > raw * 0.8:
            ok = False
    return ok, "; ".join(out)


WALK_CASES = [("walker-smoke", t_walker_smoke), ("walker-struck", t_walker_struck)]


def smoke(c):
    """`dummies on` with a Level 1 dummy for 60 s must produce no errors."""
    c.reset()
    m = c.srv.mark()
    c.srv.cmd("/backrooms dummies on")
    time.sleep(1)
    try:
        c.place(level="1")
    except RuntimeError as e:
        return False, str(e)
    time.sleep(60)
    c.reset()
    c.srv.cmd("/backrooms dummies off")
    time.sleep(1)
    bad = [l for l in c.srv.since(m) if re.search(r"error|exception", l, re.I)]
    return not bad, "dummies on + Level 1 dummy for 60 s: %d error lines%s" % (len(bad), "".join("\n  " + b[:200] for b in bad[:3]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mods", required=True)
    ap.add_argument("--data")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--no-smoke", action="store_true")
    ap.add_argument("--port", type=int, default=42733)
    ap.add_argument("--groups", choices=("all", "smoke"), help="all: every case group and the smoke (what no --only does); smoke: only the 60 s dummies smoke")
    ap.add_argument("--rerun-failed", type=int, default=0, metavar="N", help="rerun each failed case up to N more times on the same server (the placement cases are flaky)")
    a = ap.parse_args()
    if a.groups and a.only:
        sys.exit("--groups and --only are exclusive")
    data = a.data or tempfile.mkdtemp(prefix="aitest-")
    os.makedirs(data, exist_ok=True)
    only = set(a.only.split(",")) if a.only else None
    if a.groups == "smoke":
        only = {"dummies-smoke"}
    if only and "p1" in only:
        only = (only - {"p1"}) | {n for n, _ in P1_CASES}
    if only and "p26" in only:
        only = (only - {"p26"}) | {n for n, _ in P26_CASES}
    if only and "p7" in only:
        only = (only - {"p7"}) | {n for n, _ in P7_CASES}
    if only and "p7-stealer" in only:
        only = (only - {"p7-stealer"}) | {n for n, _ in STEALER_CASES}
    if only and "iso" in only:
        only = (only - {"iso"}) | {n for n, _ in ISO_CASES}
    if only and "felt" in only:
        only = (only - {"felt"}) | {n for n, _ in FELT_CASES}
    if only and "needs" in only:
        only = (only - {"needs"}) | {n for n, _ in NEEDS_CASES}
    if only and "path" in only:
        only = (only - {"path"}) | {n for n, _ in PATH_CASES}
    if only and "prog" in only:
        only = (only - {"prog"}) | {n for n, _ in PROG_CASES}
    if only and "walk" in only:
        only = (only - {"walk"}) | {n for n, _ in WALK_CASES}
    if only and "iso-hound" in only:
        only = (only - {"iso-hound"}) | {n for n, _ in ISO_HOUND_CASES}
    if only:
        # A mistyped name would otherwise boot the server (up to 15 minutes), run nothing and exit 0
        known = {n for n, _ in CASES + P1_CASES + P26_CASES + P7_CASES + ISO_CASES + ISO_HOUND_CASES + FLICKER_CASES + STEALER_CASES + FELT_CASES + NEEDS_CASES + PATH_CASES + PROG_CASES + WALK_CASES} | {"p1-no-errors", "dummies-smoke"}
        if only - known:
            sys.exit("unknown case(s): " + ", ".join(sorted(only - known)))
    started = time.time()
    srv = Server(a.mods, os.path.join(data, "vs"), a.port)
    results = []
    died = None
    try:
        if not srv.ready.wait(900):
            print("FAIL server never became ready")
            return 2
        time.sleep(5)
        c = Ctx(srv)
        p1_start = srv.mark()
        for name, fn in CASES + P1_CASES + P26_CASES + P7_CASES + ISO_CASES + ISO_HOUND_CASES + FLICKER_CASES + STEALER_CASES + FELT_CASES + NEEDS_CASES + PATH_CASES + PROG_CASES + WALK_CASES:
            if only and name not in only:
                continue
            t0 = time.time()
            try:
                if name == "p1-no-errors":
                    bad = [l for l in srv.since(p1_start) if ERR_RE.search(l) and "perceive" not in l]
                    ok, ev = not bad, "%d error/exception lines in the p1 run%s" % (len(bad), "".join("\n  " + b[:200] for b in bad[:5]))
                else:
                    ok, ev = fn(c)
            except ServerDied as e:
                died = str(e)
                results.append((name, False))
                print("FAIL %s (%.0fs): SERVER DIED: %s" % (name, time.time() - t0, died), flush=True)
                break
            except Exception as e:  # noqa: BLE001
                ok, ev = False, "harness error: %r" % (e,)
            results.append((name, ok))
            print("%s %s (%.0fs): %s" % ("SKIPPED" if ok is None else "PASS" if ok else "FAIL", name, time.time() - t0, ev), flush=True)
        if (not only or a.groups == "smoke") and not a.no_smoke and not died:
            ok, ev = smoke(c)
            results.append(("dummies-smoke", ok))
            print("%s dummies-smoke: %s" % ("PASS" if ok else "FAIL", ev), flush=True)
        if a.rerun_failed and not died:
            fns = dict(CASES + P1_CASES + P26_CASES + P7_CASES + ISO_CASES + ISO_HOUND_CASES + FLICKER_CASES + STEALER_CASES + FELT_CASES + NEEDS_CASES + PATH_CASES + PROG_CASES + WALK_CASES)
            fns["dummies-smoke"] = smoke
            for i, (name, ok0) in enumerate(list(results)):
                if ok0 is not False or not fns.get(name):
                    continue
                for attempt in range(1, a.rerun_failed + 1):
                    t0 = time.time()
                    try:
                        c.reset()
                        ok, ev = fns[name](c)
                    except ServerDied as e:
                        died = str(e)
                        print("FAIL %s rerun %d (%.0fs): SERVER DIED: %s" % (name, attempt, time.time() - t0, died), flush=True)
                        break
                    except Exception as e:  # noqa: BLE001
                        ok, ev = False, "harness error: %r" % (e,)
                    print("%s %s rerun %d (%.0fs): %s" % ("SKIPPED" if ok is None else "PASS" if ok else "FAIL", name, attempt, time.time() - t0, ev), flush=True)
                    if ok:
                        results[i] = (name, True)
                        print("RERUN-PASSED %s" % name, flush=True)
                        break
                if died:
                    break
        if not died:
            c.reset()
    except ServerDied as e:
        died = str(e)
        print("FAIL SERVER DIED: " + died, flush=True)
    finally:
        srv.stop()
        with open(os.path.join(data, "aitest.log"), "w", encoding="utf-8") as f:
            f.write("\n".join(srv.lines))
    if died:
        print("*** SERVER DIED: %s. Last 40 lines of the server log:" % died)
        logs = os.path.join(data, "vs", "Logs", "server-main.log")
        try:
            with open(logs, encoding="utf-8", errors="replace") as f:
                tail = f.read().splitlines()[-40:]
        except OSError:
            tail = srv.lines[-40:]
        print(chr(10).join("  " + l for l in tail))
        crash = os.path.join(data, "vs", "Logs", "server-crash.log")
        if os.path.exists(crash):
            print("  (see also %s)" % crash)
    errors = [l for l in srv.lines if re.search(r"\[backrooms\].*(error|exception)|exception.*backrooms", l, re.I)]
    print("log: %d lines, %d backrooms error/exception lines%s" % (len(srv.lines), len(errors), "".join("\n  " + e[:200] for e in errors[:5])))
    failed = [n for n, ok in results if ok is False]
    print("%d/%d passed in %.0f s; log %s" % (len(results) - len(failed), len(results), time.time() - started, os.path.join(data, "aitest.log")))
    if not a.keep and not a.data:
        shutil.rmtree(data, ignore_errors=True)
    for n, ok in results:
        print("  %-8s %s" % ("SKIPPED" if ok is None else "PASS" if ok else "FAIL", n))
    return 1 if failed or errors or died or not results else 0


if __name__ == "__main__":
    sys.exit(main())
