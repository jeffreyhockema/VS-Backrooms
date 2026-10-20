"""Headless perception tests (entity AI overhaul, batch P0; docs/design/entity-ai-overhaul/README.md, 4.5).

Starts a dedicated server with the built mod, puts straw dummies and a Hound down with `/backrooms dummy ...` and
`/backrooms perceive ...`, parses the `[backrooms] perceive` log lines and asserts what the Hound sees, hears and
senses.

    python tools/aitest/run.py --mods <Mods dir> [--data <dir>] [--keep] [--only <test>[,<test>]]

Exits non-zero if any case fails. The full console log goes to <data>/aitest.log.
"""
import argparse
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

    def __init__(self, c, code, kind, dist, light=0, level=LEVEL, min_band=None, ident=True):
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
    # (The hound is put down at a random angle: the maze may not give a clear line, so try several spots)
    for dist in (14, 14, 14, 10, 10, 8):
        e = Enc(c, "hound", "stalk", dist, light=14, min_band=("Approach", "Threshold"))
        ok = e.wait_for(lambda: e.has("Stalk", "Hunt"), 8)
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


P7_CASES = [("p7-hound-struck", t_p7_hound_struck), ("p7-bacteria-struck", t_p7_bacteria_struck)]



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
    a = ap.parse_args()
    data = a.data or tempfile.mkdtemp(prefix="aitest-")
    os.makedirs(data, exist_ok=True)
    only = set(a.only.split(",")) if a.only else None
    if only and "p1" in only:
        only = (only - {"p1"}) | {n for n, _ in P1_CASES}
    if only and "p26" in only:
        only = (only - {"p26"}) | {n for n, _ in P26_CASES}
    if only and "p7" in only:
        only = (only - {"p7"}) | {n for n, _ in P7_CASES}
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
        for name, fn in CASES + P1_CASES + P26_CASES + P7_CASES:
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
        if not only and not a.no_smoke and not died:
            ok, ev = smoke(c)
            results.append(("dummies-smoke", ok))
            print("%s dummies-smoke: %s" % ("PASS" if ok else "FAIL", ev), flush=True)
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
    return 1 if failed or errors or died else 0


if __name__ == "__main__":
    sys.exit(main())
