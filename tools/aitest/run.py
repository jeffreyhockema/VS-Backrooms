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
        self.p.stdin.write((c + "\r\n").encode("utf-8"))
        self.p.stdin.flush()

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
    a = ap.parse_args()
    data = a.data or tempfile.mkdtemp(prefix="aitest-")
    os.makedirs(data, exist_ok=True)
    only = set(a.only.split(",")) if a.only else None
    started = time.time()
    srv = Server(a.mods, os.path.join(data, "vs"))
    results = []
    try:
        if not srv.ready.wait(900):
            print("FAIL server never became ready")
            return 2
        time.sleep(5)
        c = Ctx(srv)
        for name, fn in CASES:
            if only and name not in only:
                continue
            t0 = time.time()
            try:
                ok, ev = fn(c)
            except Exception as e:  # noqa: BLE001
                ok, ev = False, "harness error: %r" % (e,)
            results.append((name, ok))
            print("%s %s (%.0fs): %s" % ("PASS" if ok else "FAIL", name, time.time() - t0, ev), flush=True)
        if not only and not a.no_smoke:
            ok, ev = smoke(c)
            results.append(("dummies-smoke", ok))
            print("%s dummies-smoke: %s" % ("PASS" if ok else "FAIL", ev), flush=True)
        c.reset()
    finally:
        srv.stop()
        with open(os.path.join(data, "aitest.log"), "w", encoding="utf-8") as f:
            f.write("\n".join(srv.lines))
    errors = [l for l in srv.lines if re.search(r"\[backrooms\].*(error|exception)|exception.*backrooms", l, re.I)]
    print("log: %d lines, %d backrooms error/exception lines%s" % (len(srv.lines), len(errors), "".join("\n  " + e[:200] for e in errors[:5])))
    failed = [n for n, ok in results if not ok]
    print("%d/%d passed in %.0f s; log %s" % (len(results) - len(failed), len(results), time.time() - started, os.path.join(data, "aitest.log")))
    if not a.keep and not a.data:
        shutil.rmtree(data, ignore_errors=True)
    return 1 if failed or errors else 0


if __name__ == "__main__":
    sys.exit(main())
