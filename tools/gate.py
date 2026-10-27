#!/usr/bin/env python3
"""The one-command gate: every automated check the project has, headless, one report.

    python tools/gate.py [--only a,b] [--skip a,b] [--zip] [--fast] [--port-base 42801] [--update-baselines]

Stages (in this order): generators, lang, build, boot, mapgen, scorecard, oldworld, harness, zip (zip only with --zip).
Each is timed and ends pass, FAIL or skipped with a one-line reason. The report goes to review/gate/<yyyyMMdd-HHmm>.md
(and review/gate/latest.md) and is printed. The exit code is non-zero if any stage FAILs. See docs/DEVELOPING.md "The gate".

The gate stops only servers it started, by PID (never by image name), and never touches a live save: the old-world stage
works on a copy of the save named in tools/gate.config.json.
"""
import argparse
import concurrent.futures as cf
import datetime
import glob
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGES = ["generators", "lang", "build", "boot", "mapgen", "scorecard", "oldworld", "harness", "zip"]
FAST = ["generators", "lang", "build", "boot", "harness"]
TAG = "gate"
HASH_VERSIONS = [1, 9, 10, 11]          # past layout versions, always checked; the current one is added
DEFAULT_CONFIG = {"oldWorldSave": "C:/Users/icebu/AppData/Roaming/VintagestoryData/Saves/sunny cave tales.vcdbs"}
NEVER_TOUCH = ("creepy kingdom",)       # the user's live save
SCRATCH = os.environ.get("BACKROOMS_SCRATCH") or os.path.join(os.environ.get("TEMP", tempfile.gettempdir()), "backrooms-build")
WORK = os.path.join(os.environ.get("TEMP", tempfile.gettempdir()), "backrooms-gate")
MODS = os.path.join(SCRATCH, "build-" + TAG, "Mods")
MAPGEN = os.path.join(SCRATCH, "mapgen-" + TAG, "mapgen.exe")
BASELINES = os.path.join(REPO, "tools", "gate.hashes.json")
CONFIG = os.path.join(REPO, "tools", "gate.config.json")

PASS, FAIL, SKIP = "pass", "FAIL", "skipped"


class Stage:
    def __init__(self, name):
        self.name, self.status, self.reason, self.secs, self.detail = name, SKIP, "", 0.0, []
        self.raw = []          # lines written into the report as they are (a table)

    def note(self, line):
        self.detail.append(line)


def say(s=""):
    print(s, flush=True)


def vs_dir():
    d = os.environ.get("VINTAGE_STORY") or r"G:\Games\Vintagestory"
    return d


def bash():
    for c in (r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files (x86)\Git\bin\bash.exe", shutil.which("bash")):
        if c and os.path.exists(c) and "system32" not in c.lower():
            return c
    raise SystemExit("git bash not found")


def run(cmd, cwd=REPO, timeout=1800, env=None, **kw):
    """Runs a command; returns (code, output text). Kills the process tree on timeout."""
    e = dict(os.environ)
    e["VINTAGE_STORY"] = vs_dir()
    e["PYTHONIOENCODING"] = "utf-8"
    if env:
        e.update(env)
    p = subprocess.Popen(cmd, cwd=cwd, env=e, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kw)
    try:
        out, _ = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        kill_tree(p.pid)
        out, _ = p.communicate()
        return 124, out.decode("utf-8", "replace") + "\n[timed out after %ds]" % timeout
    return p.returncode, out.decode("utf-8", "replace")


def kill_tree(pid):
    """Stops a process we started, by PID (and its children). Never by image name."""
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def git_status():
    return run(["git", "status", "--porcelain"], timeout=120)[1]


def current_version():
    s = open(os.path.join(REPO, "src", "Worldgen", "WorldLayout.cs"), encoding="utf-8").read()
    return int(re.search(r"CurrentVersion\s*=\s*(\d+)", s).group(1))


def csproj_version():
    s = open(os.path.join(REPO, "Backrooms.csproj"), encoding="utf-8").read()
    return re.search(r"<Version>([^<]+)</Version>", s).group(1)


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


# ------------------------------------------------------------------ a server we started

class Srv:
    def __init__(self, data, port, seed=None, world_config=True):
        exe = os.path.join(vs_dir(), "VintagestoryServer.exe")
        if not os.path.exists(exe):
            raise RuntimeError("VintagestoryServer.exe not found in " + vs_dir())
        if world_config:
            cfg = "{ Port: %d, WorldConfig: { Seed: '%s', WorldType: 'backrooms', PlayStyle: 'backrooms' } }" % (port, seed)
        else:
            cfg = "{ Port: %d }" % port
        self.lines, self.lock, self.ready, self.data = [], threading.Lock(), threading.Event(), data
        self.p = subprocess.Popen([exe, "--dataPath", data, "--addModPath", MODS.replace("\\", "/"), "--withconfig", cfg],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
        self.pid = self.p.pid
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        for raw in iter(self.p.stdout.readline, b""):
            s = raw.decode("utf-8", "replace").rstrip()
            with self.lock:
                self.lines.append(s)
            if "Dedicated Server now running" in s or "Server running" in s:
                self.ready.set()

    def snapshot(self):
        with self.lock:
            return list(self.lines)

    def wait_ready(self, timeout=900):
        end = time.time() + timeout
        while time.time() < end:
            if self.ready.wait(2):
                return True
            if self.p.poll() is not None:
                return False
        return False

    def cmd(self, c):
        with self.lock:
            self.lines.append(">>> " + c)
        self.p.stdin.write((c + "\r\n").encode("utf-8"))
        self.p.stdin.flush()

    def wait_line(self, pred, mark, timeout):
        end = time.time() + timeout
        seen = mark
        while time.time() < end:
            with self.lock:
                chunk = self.lines[seen:]
                seen += len(chunk)
            for l in chunk:
                if pred(l):
                    return l
            if self.p.poll() is not None:
                return None
            time.sleep(0.3)
        return None

    def stop(self):
        try:
            if self.p.poll() is None:
                self.cmd("/stop")
                self.p.wait(240)
        except Exception:  # noqa: BLE001
            pass
        if self.p.poll() is None:
            kill_tree(self.pid)
        try:
            self.p.wait(30)
        except Exception:  # noqa: BLE001
            pass
        self.reader.join(15)

    def logs(self):
        """Everything the server wrote: its console plus the log files in the data folder."""
        out = self.snapshot()
        for f in glob.glob(os.path.join(self.data, "Logs", "*.log")):
            try:
                with open(f, encoding="utf-8", errors="replace") as fh:
                    out += fh.read().splitlines()
            except OSError:
                pass
        return out


MISSING_RE = re.compile(r"Found (\d+) missing (blocks|Items|items|entities|Entities)")
BAD_LINE_RE = re.compile(r"\[backrooms\].*(error|exception)|exception.*backrooms|\[Server (Error|Fatal)\]|^\s+at \S+\(", re.I)
WARN_RE = re.compile(r"\[Server Warning\].*(unknown|could not load|couldn'?t load|failed to load)|(unknown|could not load).*(recipe|item|block|collectible)", re.I)


def scan_log(lines):
    """Returns (problems, counts) for a booted server's log: missing blocks/items, error lines, recipe/item warnings."""
    problems, missing_seen = [], 0
    for l in lines:
        if l.startswith(">>>"):
            continue
        m = MISSING_RE.search(l)
        if m:
            missing_seen += 1
            if int(m.group(1)) > 0:
                problems.append("missing: " + l.strip()[:200])
        elif re.search(r"\bmissing (blocks|items)\b", l, re.I) and re.search(r"[1-9]\d* missing|missing [^0-9]*[1-9]", l):
            problems.append("missing: " + l.strip()[:200])
        elif BAD_LINE_RE.search(l):
            problems.append("error: " + l.strip()[:200])
        elif WARN_RE.search(l):
            problems.append("warning: " + l.strip()[:200])
    if not missing_seen:
        problems.append("no 'Found N missing blocks/Items' lines in the log (did the boot finish?)")
    return list(dict.fromkeys(problems)), missing_seen


# ------------------------------------------------------------------ stages

def stage_generators(st, ctx):
    before = git_status()
    bad = []
    for g in ("gen_guide", "gen_notes", "gen_dialogue"):
        t0 = time.time()
        code, out = run([sys.executable, "tools/%s.py" % g, "--check"], timeout=900)
        tail = [l for l in out.strip().splitlines() if l.strip()][-4:]
        st.note("%s --check: exit %d (%.0fs)%s" % (g, code, time.time() - t0, "".join("\n    " + l[:200] for l in tail)))
        if code != 0:
            bad.append(g)
    if git_status() != before:
        bad.append("the checks changed the tree")
        st.note("git status differs after the checks")
    if bad:
        return FAIL, "failed: " + ", ".join(bad)
    return PASS, "gen_guide, gen_notes, gen_dialogue --check clean"


def _no_dup_hook(pairs):
    seen, dup = set(), []
    for k, _ in pairs:
        if k in seen:
            dup.append(k)
        seen.add(k)
    if dup:
        raise ValueError("duplicate keys: " + ", ".join(dup[:8]) + (" ..." if len(dup) > 8 else ""))
    return dict(pairs)


def stage_lang(st, ctx):
    bad = []
    codes = [a["code"] for a in load_json(os.path.join(REPO, "worldconfig.json"), {}).get("worldConfigAttributes", [])]
    if len(codes) != 6:
        bad.append("worldconfig.json has %d settings (expected 6)" % len(codes))
    files = sorted(glob.glob(os.path.join(REPO, "assets", "*", "lang", "*.json")))
    for f in files:
        rel = os.path.relpath(f, REPO).replace("\\", "/")
        raw = open(f, "rb").read()
        text = raw.decode("utf-8-sig")
        is_es = re.search(r"/(es-419|es-es)\.json$", rel) and "backrooms/lang" in rel
        is_en = rel.endswith("backrooms/lang/en.json")
        if is_es and not raw.startswith(b"\xef\xbb\xbf"):
            bad.append(rel + ": missing the BOM")
        if is_es and not text.lstrip().startswith("//"):
            bad.append(rel + ": does not start with // lines")
        if is_en and (raw.startswith(b"\xef\xbb\xbf") or "//" in text.split("\n", 1)[0]):
            bad.append(rel + ": en.json must be plain JSON")
        stripped = "\n".join("" if l.lstrip().startswith("//") else l for l in text.split("\n"))
        try:
            d = json.loads(stripped, object_pairs_hook=_no_dup_hook)
        except ValueError as e:
            bad.append("%s: %s" % (rel, str(e)[:160]))
            continue
        extra = ""
        if "/lang/worldconfig-" in rel:
            miss = [c for c in codes if "worldattribute-" + c not in d]
            if miss:
                bad.append("%s: missing worldattribute keys for %s" % (rel, ", ".join(miss)))
            extra = ", %d settings" % (len(codes) - len(miss))
        st.note("%s: %d keys%s" % (rel, len(d), extra))
    if not files:
        bad.append("no lang files found")
    # every name a player can read exists (tools/langcheck.py): blocks, items, entities, settings, code strings, handbook
    r = subprocess.run([sys.executable, os.path.join(REPO, "tools", "langcheck.py")], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        for l in r.stdout.splitlines():
            if l.startswith("["):
                bad.append("langcheck " + l)
        if not any(b.startswith("langcheck") for b in bad):
            bad.append("langcheck failed: " + (r.stderr or r.stdout).strip()[-300:])
    if bad:
        for b in bad:
            st.note("PROBLEM " + b)
        return FAIL, "%d problem(s): %s" % (len(bad), bad[0])
    return PASS, "%d lang files parse, no duplicate keys, six settings in the worldconfig lang, every player-facing name present (langcheck)" % len(files)


def stage_build(st, ctx):
    code, out = run([bash(), "tools/locked.sh", "mod", TAG], timeout=1800)
    errs = [l for l in out.splitlines() if re.search(r"\berror [A-Za-z]+\d+:", l)]
    for l in out.strip().splitlines()[-6:]:
        st.note(l[:220])
    dll = os.path.join(MODS, "backroomsss", "Backrooms.dll")
    if code != 0 or errs or not os.path.exists(os.path.join(MODS, "backroomsss")):
        ctx["build_ok"] = False
        return FAIL, "build failed (exit %d)%s" % (code, ": " + errs[0].strip()[:160] if errs else "")
    ctx["build_ok"] = True
    return PASS, "Debug build, 0 errors"


def _need_build(ctx):
    if ctx.get("build_ok") is False:
        return "the build failed"
    if not os.path.isdir(os.path.join(MODS, "backroomsss")):
        return "no build at %s (run the build stage)" % MODS
    return None


def _datadir(ctx, name):
    d = os.path.join(ctx["work"], name)
    os.makedirs(d, exist_ok=True)
    return d


def stage_boot(st, ctx):
    why = _need_build(ctx)
    if why:
        return SKIP, why
    seed = str(random.randint(1000, 99999999))
    srv = Srv(_datadir(ctx, "boot"), ctx["port"], seed)
    try:
        if not srv.wait_ready(900):
            st.detail += ["  " + l[:200] for l in srv.snapshot()[-15:]]
            return FAIL, "server never became ready (seed %s)" % seed
        time.sleep(10)
    finally:
        srv.stop()
    problems, _ = scan_log(srv.logs())
    st.note("seed %s, %d console lines" % (seed, len(srv.snapshot())))
    for p in problems:
        st.note("PROBLEM " + p)
    if problems:
        return FAIL, "%d problem(s): %s" % (len(problems), problems[0][:150])
    return PASS, "fresh seed %s booted: 0 missing blocks/items, 0 error lines, 0 recipe/item warnings" % seed


def stage_oldworld(st, ctx):
    why = _need_build(ctx)
    if why:
        return SKIP, why
    cfg = dict(DEFAULT_CONFIG)
    cfg.update(load_json(CONFIG, {}))
    save = cfg["oldWorldSave"]
    if any(n in save.lower() for n in NEVER_TOUCH):
        return FAIL, "refusing to use a live save: " + save
    if not os.path.exists(save):
        return SKIP, "OLD-WORLD SAVE NOT FOUND, stage not run (set oldWorldSave in tools/gate.config.json): " + save
    data = _datadir(ctx, "oldworld")
    os.makedirs(os.path.join(data, "Saves"), exist_ok=True)
    shutil.copyfile(save, os.path.join(data, "Saves", "default.vcdbs"))
    srv = Srv(data, ctx["port"] + 2, world_config=False)
    rate = None
    try:
        if not srv.wait_ready(900):
            st.detail += ["  " + l[:200] for l in srv.snapshot()[-15:]]
            return FAIL, "server never became ready on the old world"
        time.sleep(10)
        mark = len(srv.snapshot())
        srv.cmd("/backrooms ratecheck 1 heartland 20")
        rate = srv.wait_line(lambda l: re.search(r"ratecheck Level .*bodies", l), mark, 60)
        time.sleep(2)
    finally:
        srv.stop()
    problems, _ = scan_log(srv.logs())
    st.note("copied %s" % save)
    st.note("ratecheck: " + (rate.strip()[:200] if rate else "no answer"))
    for p in problems:
        st.note("PROBLEM " + p)
    if not rate:
        problems.append("ratecheck 1 heartland 20 gave no answer")
    if problems:
        return FAIL, "%d problem(s): %s" % (len(problems), problems[0][:150])
    return PASS, "old world loaded: 0 missing, 0 errors; ratecheck answered"


# ---- mapgen

def mg(args, env=None, timeout=900):
    wd = tempfile.mkdtemp(prefix="mg-", dir=WORK)
    try:
        e = {"SPAWN": "16000"}
        e.update(env or {})
        return run([MAPGEN] + args, cwd=wd, env=e, timeout=timeout)
    finally:
        shutil.rmtree(wd, ignore_errors=True)


def parse_validate(out, lv):
    m = {"noArrival": 0, "doorsToNowhere": 0, "doorsBlocked": 0, "badElevators": 0, "decorFacingWalls": 0, "unreachable": 0, "walkable": 0}
    for l in out.splitlines():
        if l.strip() == "no arrival":
            m["noArrival"] += 1
        r = re.match(r"doorways to nowhere: (\d+), doorways blocked by props: (\d+), bad elevators: (\d+), decor facing walls: (\d+)", l)
        if r:
            for k, v in zip(("doorsToNowhere", "doorsBlocked", "badElevators", "decorFacingWalls"), r.groups()):
                m[k] += int(v)
        r = re.match(r"Level %d: (\d+) walkable tiles, (\d+) unreachable" % lv, l)
        if r:
            m["walkable"] += int(r.group(1))
            m["unreachable"] += int(r.group(2))
    return m


def parse_deep(out):
    m = {}
    for l in out.splitlines():
        r = re.match(r"(.+?)\s*: found (\d+)/(\d+)(.*)", l)
        if not r:
            continue
        k = r.group(1).strip()
        m[k + " found"] = int(r.group(2))
        for name, v in re.findall(r"(wrong level|trapped|in snackrooms|really snackrooms|ok) (\d+)", r.group(4)):
            if name in ("wrong level", "trapped"):
                m[k + " " + name] = int(v)
    return m


def parse_shortcuts(out):
    m = {}
    for l in out.splitlines():
        r = re.match(r"^  (\S.*?)\s{2,}(\d+)\s*$", l)
        if r:
            m[r.group(1)] = int(r.group(2))
    return m


def parse_hash(out):
    h = re.search(r"^layout hash ([0-9a-f]{16})", out, re.M)
    f = re.search(r"^far places hash ([0-9a-f]{16})", out, re.M)
    return (h.group(1) if h else None, f.group(1) if f else None)


HIGHER_BETTER = (" found", "walkable")


def compare_metrics(kind, cur, base, problems, notes):
    """FAIL-worthy: a bad count above its baseline (or a found count below). Improvements are noted."""
    for k in base:
        if k not in cur and k != "walkable":
            problems.append("%s %s: missing from the output (baseline %s)" % (kind, k, base[k]))
    for k, v in cur.items():
        if k not in base:
            continue
        b = base[k]
        if k.endswith(HIGHER_BETTER) or k == "walkable":
            if k == "walkable":
                continue
            worse, better = v < b, v > b
        else:
            worse, better = v > b, v < b
        if worse:
            problems.append("%s %s: %s (baseline %s)" % (kind, k, v, b))
        elif better:
            notes.append("%s %s improved: %s (baseline %s)" % (kind, k, v, b))


def stage_mapgen(st, ctx):
    code, out = run([bash(), "tools/locked.sh", "mapgen", TAG], timeout=1800)
    if code != 0 or not os.path.exists(MAPGEN):
        for l in out.strip().splitlines()[-6:]:
            st.note(l[:220])
        return FAIL, "the mapgen harness did not build"
    base = ctx["baselines"]
    cur_v = current_version()
    new_base = json.loads(json.dumps(base))
    problems, notes, recorded = [], [], []
    versions = HASH_VERSIONS + [cur_v]
    with cf.ThreadPoolExecutor(4) as ex:
        hash_f = {v: ex.submit(mg, ["1", "6", "layouthash"], {"LAYOUT_VERSION": str(v)}) for v in versions}
        val_f = {lv: ex.submit(mg, ["12345", "24", "validatelevel", str(lv)]) for lv in range(21)}
        validate_f = ex.submit(mg, ["12345", "24", "validate"])
        deep_f = ex.submit(mg, ["12345", "24", "deep"])
        links_f = ex.submit(mg, ["12345", "24", "links"])
        short_f = ex.submit(mg, ["12345", "24", "shortcuts"])

        # layout hashes
        bh = new_base.setdefault("layoutHashes", {})
        for v in versions:
            c, o = hash_f[v].result()
            h, f = parse_hash(o)
            if c != 0 or not h or not f:
                problems.append("layouthash v%d did not run (exit %d)" % (v, c))
                continue
            key = str(v)
            rec = bh.get(key)
            cur = {"layout": h, "far": f}
            st.note("layouthash v%d: layout %s, far places %s" % (v, h, f))
            if rec is None:
                bh[key] = cur
                recorded.append("layout hash v%d" % v)
            elif rec != cur:
                if v < cur_v:
                    problems.append("layout hash v%d CHANGED: %s -> %s (a past version must stay byte-identical)" % (v, rec, cur))
                elif ctx["update"]:
                    bh[key] = cur
                    recorded.append("layout hash v%d updated" % v)
                else:
                    notes.append("current version %d hash changed %s -> %s (expected while it is in development; --update-baselines records it)" % (v, rec, cur))

        # validate by level
        bv = new_base.setdefault("validate", {})
        tot = {}
        for lv in range(21):
            c, o = val_f[lv].result()
            if c != 0:
                problems.append("validatelevel %d exit %d" % (lv, c))
                continue
            m = parse_validate(o, lv)
            if m["walkable"] <= 0:
                problems.append("validatelevel %d: no walkable tiles parsed (output format changed?)" % lv)
                continue
            for k, v in m.items():
                tot[k] = tot.get(k, 0) + v
            key = "L%d" % lv
            if key not in bv:
                bv[key] = m
                recorded.append("validate " + key)
            else:
                compare_metrics("validatelevel %d" % lv, m, bv[key], problems, notes)
                if ctx["update"]:
                    bv[key] = m
        st.note("validatelevel 0-20 (24 cells, SPAWN=16000, 2 arrivals): unreachable %d, doorways to nowhere %d, blocked %d, bad elevators %d, decor %d, no-arrival %d" % (
            tot.get("unreachable", 0), tot.get("doorsToNowhere", 0), tot.get("doorsBlocked", 0), tot.get("badElevators", 0), tot.get("decorFacingWalls", 0), tot.get("noArrival", 0)))
        c, o = validate_f.result()
        m = parse_validate(o, 0)
        if c != 0:
            problems.append("validate exit %d" % c)
        else:
            key = "spawn"
            if key not in bv:
                bv[key] = {k: v for k, v in m.items() if k != "walkable"}
                recorded.append("validate spawn")
            else:
                compare_metrics("validate (spawn window)", m, bv[key], problems, notes)
                if ctx["update"]:
                    bv[key] = {k: v for k, v in m.items() if k != "walkable"}

        # deep
        c, o = deep_f.result()
        m = parse_deep(o)
        bd = new_base.setdefault("deep", {})
        if c != 0 or not m:
            problems.append("deep did not run (exit %d)" % c)
        elif not bd:
            new_base["deep"] = m
            recorded.append("deep")
        else:
            compare_metrics("deep", m, bd, problems, notes)
            if ctx["update"]:
                new_base["deep"] = m
        st.note("deep (24 cells): %d figures" % len(m))

        # links
        c, o = links_f.result()
        lbad = []
        if c != 0:
            lbad.append("exit %d" % c)
        for l in o.splitlines():
            for a, b in re.findall(r"(\d+) of (\d+) links", l):
                if a != b:
                    lbad.append(l.strip()[:160])
            for a, b in re.findall(r"(\d+)/(\d+) the same", l):
                if a != b:
                    lbad.append(l.strip()[:160])
            if re.match(r"(ways back|damaged data):", l) and not l.rstrip().endswith("ok"):
                lbad.append(l.strip()[:160])
        if not re.search(r"save/load: read", o) or not re.search(r"\d+ of \d+ links", o) or not re.search(r"^ways back:", o, re.M):
            lbad.append("expected lines missing (output format changed?)")
        if lbad:
            problems.append("links: " + lbad[0])
        st.note("links: " + ("clean" if not lbad else "; ".join(lbad[:3])))

        # shortcuts
        c, o = short_f.result()
        m = parse_shortcuts(o)
        if c != 0 or not m:
            problems.append("shortcuts did not run (exit %d)" % c)
        else:
            ctx["shortcuts"] = m
            bs = new_base.setdefault("shortcuts", {})
            key = "v%d" % cur_v
            if key not in bs:
                bs[key] = m
                recorded.append("shortcuts " + key)
            elif bs[key] != m:
                diff = ["%s %s->%s" % (k, bs[key].get(k), m.get(k)) for k in sorted(set(bs[key]) | set(m)) if bs[key].get(k) != m.get(k)]
                notes.append("shortcut counts changed vs the recorded v%d window: %s" % (cur_v, "; ".join(diff[:6])))
                if ctx["update"]:
                    bs[key] = m
            st.note("shortcuts v%d (12 arrivals x 11 levels window): %s" % (cur_v, ", ".join("%s=%d" % (k, v) for k, v in list(m.items())[:8]) + (", ..." if len(m) > 8 else "")))
    for n in notes:
        st.note("note " + n)
    if recorded:
        st.note("recorded as new baselines in tools/gate.hashes.json: " + ", ".join(recorded))
    for p in problems:
        st.note("PROBLEM " + p)
    if new_base != base and not problems:
        with open(BASELINES, "w", encoding="utf-8", newline="\n") as f:
            json.dump(new_base, f, indent=2, sort_keys=True)
            f.write("\n")
        ctx["baselines"] = new_base
    if problems:
        return FAIL, "%d problem(s): %s" % (len(problems), problems[0][:170])
    extra = "; recorded %d new baseline(s)" % len(recorded) if recorded else ""
    return PASS, "hashes of v%s match, validate/deep within baseline, links clean%s" % (",".join(map(str, versions)), extra)


# ---- scorecard (docs/design/balance-spec.yaml)

SPEC = os.path.join(REPO, "docs", "design", "balance-spec.yaml")
RATE_RE = re.compile(r"ratecheck Level (\d+) (\w+) \(menace [\d.]+, setting (\w+), [\d.]+ h, \d+ kinds of menacing thing about \(of (\d+) allowed\)\): "
                     r"bodies ([\d.]+)/h \(glimpse ([\d.]+), stalk ([\d.]+), hunt ([\d.]+)\), sounds ([\d.]+)/h")
ARM_HEAD_RE = re.compile(r"armourtest (\S+) Level (\S+): danger ([\d.]+), hit ([\d.]+) at tier (\d+)")
ARM_LINE_RE = re.compile(r"armourtest (\S+) L(\S+) (\S+): head ([\d.]+) body ([\d.]+) legs ([\d.]+); mean ([\d.]+); blows to kill (\S+) \((\d+) to (\S+)\)")
DUMMY_RE = re.compile(r"Dummy #(\d+) at (-?\d+) (-?\d+) (-?\d+), Level (\S+), light (-?\d+)")
FELT_RE = re.compile(r"felt bodies ([\d.]+)/h")
SCALE_RE = re.compile(r"level (-?\d+), class scale ([\d.]+)")
DIFF_RE = re.compile(r'new\("(\w+)",\s*([\d.]+),\s*([\d.]+),\s*(?:true|false)(?:,\s*([\d.]+))?(?:,\s*(\d+))?(?:,\s*(\d+))?\)')
FELT_TRIES = 60


class Card:
    """The scorecard's rows: group, what, spec, measured, verdict (True ok, False FAIL, None not measured)."""

    def __init__(self):
        self.rows = []

    def add(self, group, what, spec, measured, ok):
        self.rows.append((group, what, spec, measured, ok))

    def within(self, group, what, target, got, tol_pct, abs_floor=0.0, fmt="%.1f"):
        ok = abs(got - target) <= max(abs(target) * tol_pct / 100.0, abs_floor)
        self.add(group, what, (fmt + " +-%d%%") % (target, tol_pct) if tol_pct else fmt % target, fmt % got, ok)
        return ok

    def table(self):
        mark = {True: "ok", False: "FAIL", None: "not measured"}
        out = ["| Group | Row | Spec | Measured | |", "|---|---|---|---|---|"]
        for g, w, s, m, ok in self.rows:
            out.append("| %s | %s | %s | %s | %s |" % (g, w, s, m, mark[ok]))
        return out


def _ask(srv, command, done, timeout=60, settle=0.6):
    """Sends a command; returns the lines that came after it once `done(line)` matched one (None if it never did)."""
    mark = len(srv.snapshot())
    srv.cmd(command)
    if srv.wait_line(done, mark, timeout) is None:
        return None
    time.sleep(settle)
    return srv.snapshot()[mark:]


def _ratecheck(srv, lid, band, hours):
    lines = _ask(srv, "/backrooms ratecheck %s %s %s" % (lid, band, hours), lambda l: RATE_RE.search(l) or "No rolls" in l or "Give a level" in l)
    for l in lines or []:
        g = RATE_RE.search(l)
        if g:
            return {"bodies": float(g.group(5)), "sounds": float(g.group(9)), "kinds_allowed": int(g.group(4)), "setting": g.group(3)}
    return None


def _armour(srv, entity, level):
    """({danger, hit, tier}, {set: {mean, blows, fewest}}) from one armourtest command, or (None, {})."""
    lines = _ask(srv, "/backrooms armourtest %s %s" % (entity, level), lambda l: re.search(r" plate-iron: head", l), 30)
    head, rows = None, {}
    for l in lines or []:
        g = ARM_HEAD_RE.search(l)
        if g and head is None:
            head = {"danger": float(g.group(3)), "hit": float(g.group(4)), "tier": int(g.group(5))}
        g = ARM_LINE_RE.search(l)
        if g and g.group(3) not in rows:
            rows[g.group(3)] = {"mean": float(g.group(7)), "blows": g.group(8), "fewest": int(g.group(9))}
    return head, rows


def _place_dummy(srv, level, attempts=8):
    """A straw dummy at one of the level's arrival spots (the chunk may need a few tries to load). (x, z) or None."""
    key = int(time.time() * 1000) % 100000
    for k in range(attempts):
        if k == 4:
            key = int(time.time() * 1000) % 100000
        lines = _ask(srv, "/backrooms dummy place %s %d" % (level, key), lambda l: DUMMY_RE.search(l) or "not loaded" in l.lower() or "Found nowhere" in l, 25, 0.2)
        for l in lines or []:
            g = DUMMY_RE.search(l)
            if g:
                return int(g.group(2)), int(g.group(4))
        time.sleep(10)
    return None


def _felt(srv, band):
    lines = _ask(srv, "/backrooms feltrate here %s %d" % (band, FELT_TRIES), lambda l: FELT_RE.search(l), 120, 0.2)
    for l in lines or []:
        g = FELT_RE.search(l)
        if g:
            return float(g.group(1))
    return None


def _blows_ok(spec_blows, got_blows, tol_pct):
    if str(spec_blows) == "never" or got_blows == "never":
        return str(spec_blows) == got_blows
    s, g = float(spec_blows), float(got_blows)
    return abs(g - s) <= max(abs(s) * tol_pct / 100.0, 0.15)


def _anchor_check(a, rows):
    """(ok, spec text, measured text) for one lethality anchor, from the entity's armourtest rows at that level."""
    r, none = rows.get(a["set"]), rows.get("none")
    if r is None or none is None:
        return False, a["why"], "no armourtest line"
    if "blows_ceil" in a:
        lo, hi = a["blows_ceil"]
        b = math.ceil(float(r["blows"]) - 1e-9) if r["blows"] != "never" else 999
        return lo <= b <= hi, "%d to %d blows" % (lo, hi), "%.1f blows (%d)" % (float(r["blows"]), b)
    if "hit_ratio_max" in a:
        ratio = r["mean"] / none["mean"] if none["mean"] else 9
        return ratio <= a["hit_ratio_max"], "<= %.2f x the unarmoured blow" % a["hit_ratio_max"], "%.2f x" % ratio
    if "fewest_min" in a:
        return r["fewest"] >= a["fewest_min"], ">= %d blows even on the worst piece" % a["fewest_min"], "%d" % r["fewest"]
    return None, a["why"], "unknown anchor kind"


def _shortcut_counts(st, ctx):
    """The mapgen stage's shortcut counts, or (when only the scorecard runs) the same mapgen mode run here."""
    if ctx.get("shortcuts"):
        return ctx["shortcuts"], "this run's mapgen stage"
    code, out = run([bash(), "tools/locked.sh", "mapgen", TAG], timeout=1800)
    if code != 0 or not os.path.exists(MAPGEN):
        return None, "the mapgen harness did not build"
    c, o = mg(["12345", "24", "shortcuts"])
    m = parse_shortcuts(o)
    return (m or None), "mapgen 12345 24 shortcuts, run by the scorecard"


def stage_scorecard(st, ctx):
    why = _need_build(ctx)
    if why:
        return SKIP, why
    try:
        import yaml
    except ImportError:
        return FAIL, "PyYAML is not installed (pip install pyyaml)"
    try:
        with open(SPEC, encoding="utf-8") as f:
            spec = yaml.safe_load(f)
    except (OSError, ValueError) as e:
        return FAIL, "cannot read %s: %s" % (SPEC, e)
    card = Card()
    levels = spec["levels"]
    glob_ = spec["global"]
    problems = []

    # settings table, by the source (the Difficulties array)
    try:
        src = open(os.path.join(REPO, "src", "Entities", "MenaceSystem.cs"), encoding="utf-8").read()
        code_tab = {m.group(1): m.groups()[1:] for m in DIFF_RE.finditer(src)}
        for name, want in glob_["settings"].items():
            got = code_tab.get(name)
            if got is None:
                card.add("settings", name, "present", "missing in MenaceSystem.Difficulties", False)
                continue
            vals = [float(got[0]), float(got[1]), float(got[2] or 0), float(got[3] or 0), float(got[4] or 0)]
            wants = [want["spawns"], want["damage"], want["mix_danger"], want["cap_bonus_outer"], want["cap_bonus_heart"]]
            card.add("settings", name, "spawns %g damage %g mix %g caps %g/%g" % tuple(wants), "spawns %g damage %g mix %g caps %g/%g" % tuple(vals),
                     all(abs(a - b) < 1e-9 for a, b in zip(vals, wants)))
        extra = sorted(set(code_tab) - set(glob_["settings"]))
        if extra:
            card.add("settings", "other codes", "none", ", ".join(extra), False)
    except OSError as e:
        card.add("settings", "table", "readable", str(e), False)

    srv = Srv(_datadir(ctx, "scorecard"), ctx["port"] + 10, "12345")
    try:
        if not srv.wait_ready(900):
            st.detail += ["  " + l[:200] for l in srv.snapshot()[-15:]]
            return FAIL, "server never became ready"
        time.sleep(10)

        # ---- rolls: bodies and sounds per band, the kinds allowed
        setting_checked = False
        for lv in levels:
            lid, key = lv["id"], lv["level"]
            kinds_seen = None
            for band, row in (lv.get("bands") or {}).items():
                r = _ratecheck(srv, lid, band, 20)
                if r is None:
                    card.add("rolls", "L%s %s" % (key, band), "a ratecheck reply", "none", False)
                    continue
                if not setting_checked:
                    setting_checked = True
                    card.add("settings", "the scorecard server's setting", spec.get("setting", "normal"), r["setting"], r["setting"] == spec.get("setting", "normal"))
                for what in ("bodies", "sounds"):
                    want = row[what]
                    ok = abs(r[what] - want["target"]) <= want["target"] * want["tol_pct"] / 100.0
                    got = r[what]
                    note = ""
                    if not ok:   # the 20 hour sample is noisy: decide on 100 hours
                        r2 = _ratecheck(srv, lid, band, 100)
                        if r2:
                            got = r2[what]
                            ok = abs(got - want["target"]) <= want["target"] * want["tol_pct"] / 100.0
                            note = " (100 h)"
                    card.add("rolls", "L%s %s %s/h [%s]" % (key, band, what, want["basis"]), "%.1f +-%d%%" % (want["target"], want["tol_pct"]), "%.1f%s" % (got, note), ok)
                if kinds_seen is None:
                    kinds_seen = r["kinds_allowed"]
            if kinds_seen is None:
                r0 = _ratecheck(srv, lid, "approach", 1)
                kinds_seen = r0["kinds_allowed"] if r0 else None
            if kinds_seen is not None:
                card.add("class", "L%s kinds allowed at once [decision]" % key, str(lv["max_kinds"]), str(kinds_seen), kinds_seen == lv["max_kinds"])

        # ---- armour and danger
        armour_rows = {}
        for lv in levels:
            key = lv["level"]
            arm = lv.get("armour") or {}
            entity = arm.get("hunter") or "smiler"
            head, rows = _armour(srv, entity, key)
            armour_rows[(entity, key)] = rows
            if head is None:
                card.add("armour", "L%s %s" % (key, entity), "an armourtest reply", "none", False)
                continue
            card.within("danger", "L%s danger" % key, lv["danger"], head["danger"], 0, 0.006, "%.2f")
            if not arm:
                continue
            for s, want in arm["sets"].items():
                got = rows.get(s)
                if got is None:
                    card.add("armour", "L%s %s vs %s" % (key, entity, s), "a line", "missing", False)
                    continue
                okh = abs(got["mean"] - want["hit"]) <= max(want["hit"] * 0.05, 0.06)
                okb = _blows_ok(want["blows"], got["blows"], 5)
                card.add("armour", "L%s %s vs %s: hit / blows [measurement]" % (key, entity, s), "%.2f / %s" % (want["hit"], want["blows"]), "%.2f / %s" % (got["mean"], got["blows"]), okh and okb)
        for a in glob_.get("lethality_anchors", []):
            rows = armour_rows.get((a["entity"], a["level"]))
            if rows is None:
                _, rows = _armour(srv, a["entity"], a["level"])
            ok, spec_t, got_t = _anchor_check(a, rows)
            card.add("anchor", "%s L%s %s [decision]" % (a["entity"], a["level"], a["set"]), spec_t, got_t, ok)

        # ---- felt rates and the class scale, with a dummy in the level (only where placement is reliable)
        reliable = {"1", "2", "3", "5", "8", "9"}
        placed_any = False
        for lv in levels:
            key = lv["level"]
            felt = ((lv.get("bands") or {}).get("approach") or {}).get("felt")
            if key not in reliable:
                if felt:
                    card.add("felt", "L%s approach felt/h" % key, "%.1f +-%d%%" % (felt["target"], felt["tol_pct"]), "(dummy placement not reliable here)", None)
                if lv.get("class_scale") is not None:
                    card.add("scarcity", "L%s class scale" % key, "%g" % lv["class_scale"], "(no dummy placed here)", None)
                continue
            samples, spots = [], []
            srv.cmd("/backrooms dummy remove")
            time.sleep(1)
            for trial in range(4 if felt else 1):
                if trial >= 2 and felt and len(samples) >= 2 and abs(sum(samples) / len(samples) - felt["target"]) <= felt["target"] * felt["tol_pct"] / 100.0:
                    break    # the first two are inside: no more needed
                if trial:
                    srv.cmd("/backrooms dummy remove")
                    time.sleep(1)
                spot = _place_dummy(srv, key)
                if spot is None:
                    break
                spots.append(spot)
                placed_any = True
                if felt:
                    f = _felt(srv, "approach")
                    if f is not None:
                        samples.append(f)
            if felt:
                if samples:
                    mean = sum(samples) / len(samples)
                    card.add("felt", "L%s approach felt/h [%s]" % (key, felt["basis"]), "%.1f +-%d%%" % (felt["target"], felt["tol_pct"]),
                             "%.1f (mean of %s)" % (mean, ", ".join("%.1f" % s for s in samples)), abs(mean - felt["target"]) <= felt["target"] * felt["tol_pct"] / 100.0)
                else:
                    card.add("felt", "L%s approach felt/h" % key, "%.1f +-%d%%" % (felt["target"], felt["tol_pct"]), "no dummy could be placed", None)
            if spots and lv.get("class_scale") is not None:
                x, z = spots[0]
                lines = _ask(srv, "/backrooms classdrops supplybox %d %d 20" % (x, z), lambda l: SCALE_RE.search(l) or "No such block" in l, 30, 0.2)
                g = next((SCALE_RE.search(l) for l in lines or [] if SCALE_RE.search(l)), None)
                if g:
                    card.add("scarcity", "L%s class scale [decision]" % key, "%g" % lv["class_scale"], g.group(2), abs(float(g.group(2).replace(",", ".")) - lv["class_scale"]) < 1e-6)
                else:
                    card.add("scarcity", "L%s class scale" % key, "%g" % lv["class_scale"], "no reply", None)
            elif lv.get("class_scale") is not None:
                card.add("scarcity", "L%s class scale" % key, "%g" % lv["class_scale"], "no dummy could be placed", None)
        for lv in levels:
            key = lv["level"]
            if key not in reliable and lv.get("class_scale") is not None and not any(r[0] == "scarcity" and r[1].startswith("L%s " % key) for r in card.rows):
                card.add("scarcity", "L%s class scale" % key, "%g" % lv["class_scale"], "", None)
        srv.cmd("/backrooms dummy remove")
        time.sleep(1)
        if not placed_any:
            card.add("felt", "dummy placement (any reliable level)", "at least one dummy placed", "none placed", False)
    finally:
        srv.stop()
    for p in scan_log(srv.logs())[0]:
        if p.startswith("error"):
            problems.append(p)

    # ---- shortcuts
    counts, how = _shortcut_counts(st, ctx)
    sc = spec["shortcuts"]["counts"]
    if not counts:
        card.add("shortcuts", "counts", "mapgen shortcuts output", how, False)
    else:
        tol, floor = glob_.get("shortcut_tol_pct", 15), glob_.get("shortcut_abs_tol", 2)
        for k, want in sc.items():
            got = counts.get(k)
            if got is None:
                card.add("shortcuts", k, str(want), "missing", False)
            else:
                card.add("shortcuts", k, "%d +-%d%% (min %d)" % (want, tol, floor), str(got), abs(got - want) <= max(want * tol / 100.0, floor))

    bad = [r for r in card.rows if r[4] is False]
    na = [r for r in card.rows if r[4] is None]
    ctx["scorecard"] = card
    st.raw = card.table()
    st.note("%d rows: %d ok, %d outside the spec, %d not measured. Spec %s (status: %s). Shortcut counts from %s." % (
        len(card.rows), len(card.rows) - len(bad) - len(na), len(bad), len(na), os.path.relpath(SPEC, REPO), spec.get("status"), how))
    for r in bad:
        st.note("FAIL %s / %s: spec %s, measured %s" % (r[0], r[1], r[2], r[3]))
    for p in problems:
        st.note("PROBLEM " + p)
    if bad or problems:
        return FAIL, "%d row(s) outside the spec%s: %s" % (len(bad), " and %d error line(s)" % len(problems) if problems else "", (bad[0][0] + " / " + bad[0][1]) if bad else problems[0][:100])
    return PASS, "%d rows within the spec (%d not measured)" % (len(card.rows) - len(na), len(na))


# ---- harness

def stage_harness(st, ctx):
    why = _need_build(ctx)
    if why:
        return SKIP, why
    data = _datadir(ctx, "harness")
    args = [sys.executable, "-u", "tools/aitest/run.py", "--mods", MODS, "--data", data, "--keep", "--port", str(ctx["port"] + 1)]
    if ctx["smoke_only"]:
        args += ["--groups", "smoke"]
    else:
        args += ["--groups", "all", "--rerun-failed", "1"]
    env = dict(os.environ, VINTAGE_STORY=vs_dir(), PYTHONIOENCODING="utf-8")
    p = subprocess.Popen(args, cwd=REPO, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines, timed_out = [], False
    ctx["child"] = p
    try:
        def pump():
            for raw in iter(p.stdout.readline, b""):
                l = raw.decode("utf-8", "replace").rstrip()
                lines.append(l)
                if re.match(r"(PASS|FAIL|SKIPPED|RERUN-PASSED) ", l):
                    say("    harness: " + l[:170])
        t = threading.Thread(target=pump, daemon=True)
        t.start()
        try:
            p.wait(timeout=ctx["harness_timeout"])
        except subprocess.TimeoutExpired:
            kill_tree(p.pid)
            timed_out = True
        t.join(10)
    finally:
        ctx["child"] = None
        if p.poll() is None:
            kill_tree(p.pid)
    os.makedirs(os.path.join(REPO, "review", "gate"), exist_ok=True)
    log = os.path.join(REPO, "review", "gate", ctx["stamp"] + "-harness.txt")
    with open(log, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    if timed_out:
        return FAIL, "harness timed out after %d min (output in %s)" % (ctx["harness_timeout"] // 60, log)
    # The summary block at the end: "  PASS name" / "  FAIL name" / "  SKIPPED name"
    summary = {}
    for l in lines:
        r = re.match(r"^  (PASS|FAIL|SKIPPED)\s+(\S.*?)\s*$", l)
        if r:
            summary[r.group(2)] = r.group(1)
    reran = [l.split(" ", 1)[1] for l in lines if l.startswith("RERUN-PASSED ")]
    errors = re.search(r"log: \d+ lines, (\d+) backrooms error/exception", "\n".join(lines))
    nerr = int(errors.group(1)) if errors else None
    failed = [n for n, s in summary.items() if s == "FAIL"]
    died = [l for l in lines if "SERVER DIED" in l]
    n = len(summary)
    st.note("%d cases%s; harness output %s" % (n, " (smoke only)" if ctx["smoke_only"] else "", log))
    for n_ in reran:
        st.note("flaky: %s failed once and passed on the rerun" % n_)
    for l in lines:
        if re.match(r"FAIL ", l):
            st.note(l[:220])
    if died:
        return FAIL, "server died: " + died[0][:150]
    if not summary:
        return FAIL, "no case results (harness exit %s)" % p.returncode
    if failed:
        return FAIL, "%d of %d case(s) failed after the rerun: %s" % (len(failed), n, ", ".join(failed))
    if nerr is None:
        return FAIL, "the harness did not finish (no log summary, exit %s)" % p.returncode
    if nerr:
        st.note("backrooms error/exception lines: %d (see the harness output)" % nerr)
        return FAIL, "all %d cases passed but the server log has %d backrooms error line(s)" % (n, nerr)
    flaky = " (%d passed on rerun: %s)" % (len(reran), ", ".join(reran)) if reran else ""
    return PASS, "%d/%d cases passed, 0 backrooms error lines%s" % (n, n, flaky)


# ---- zip

def stage_zip(st, ctx):
    rel = os.path.join(REPO, "bin", "Release")
    if os.path.isdir(rel):
        shutil.rmtree(rel, ignore_errors=True)
    old = os.path.join(REPO, "bin", "backroomsss_%s.zip" % csproj_version())
    if os.path.exists(old):
        os.remove(old)
    code, out = run([bash(), "tools/locked.sh", "release", TAG], timeout=1800)
    for l in out.strip().splitlines()[-4:]:
        st.note(l[:220])
    ver = csproj_version()
    zp = os.path.join(REPO, "bin", "backroomsss_%s.zip" % ver)
    if code != 0:
        return FAIL, "the Release build failed (exit %d)" % code
    if not os.path.exists(zp):
        return FAIL, "no zip at " + zp
    with zipfile.ZipFile(zp) as z:
        names = z.namelist()
        mi = [n for n in names if n.endswith("modinfo.json")]
        zv = json.loads(z.read(mi[0]).decode("utf-8-sig")).get("version") if mi else None
        pdb = [n for n in names if n.endswith(".pdb")]
    size = os.path.getsize(zp) / 1048576
    st.note("%s (%.1f MB, %d files)" % (zp, size, len(names)))
    disk = load_json(os.path.join(REPO, "modinfo.json"), {}).get("version")
    st.note("version: csproj %s, repo modinfo.json %s, modinfo in zip %s" % (ver, disk, zv))
    if zv != ver or disk != ver:
        return FAIL, "version mismatch: csproj %s, modinfo.json %s, zip %s" % (ver, disk, zv)
    if pdb:
        return FAIL, "zip carries a pdb: " + pdb[0]
    return PASS, "%s, %.1f MB, version %s matches csproj and modinfo.json" % (os.path.relpath(zp, REPO), size, ver)


FUNCS = {"generators": stage_generators, "lang": stage_lang, "build": stage_build, "boot": stage_boot, "mapgen": stage_mapgen,
         "scorecard": stage_scorecard, "oldworld": stage_oldworld, "harness": stage_harness, "zip": stage_zip}


# ------------------------------------------------------------------ report

def fmt(secs):
    return "%dm%02ds" % (secs // 60, secs % 60)


def report(stages, total, stamp, args):
    fails = [s for s in stages if s.status == FAIL]
    head = "# Gate report %s\n\nResult: **%s** in %s. Branch %s, commit %s. Flags: %s\n\n" % (
        stamp, "FAIL (%d)" % len(fails) if fails else "PASS", fmt(total),
        run(["git", "rev-parse", "--abbrev-ref", "HEAD"], timeout=60)[1].strip(), run(["git", "rev-parse", "--short", "HEAD"], timeout=60)[1].strip(),
        " ".join(args) or "(none)")
    rows = ["| Stage | Result | Time | Reason |", "|---|---|---|---|"]
    for s in stages:
        rows.append("| %s | %s | %s | %s |" % (s.name, s.status, fmt(s.secs), s.reason.replace("|", "/")))
    body = "\n".join(rows) + "\n"
    for s in stages:
        if s.detail:
            body += "\n## %s\n\n" % s.name + "\n".join("- " + d.replace("\n", "\n  ") for d in s.detail) + "\n"
        if s.raw:
            body += "\n" + "\n".join(s.raw) + "\n"
    return head + body


def main():
    ap = argparse.ArgumentParser(description="Runs every automated check headless and writes review/gate/<stamp>.md")
    ap.add_argument("--only", help="comma list of stages: " + ",".join(STAGES))
    ap.add_argument("--skip", help="comma list of stages to skip")
    ap.add_argument("--zip", action="store_true", help="also build the Release zip")
    ap.add_argument("--fast", action="store_true", help="generators, lang, build, boot and the harness smoke only")
    ap.add_argument("--port-base", type=int, default=42801, help="first port (boot uses base, the harness base+1, the old world base+2, the scorecard base+10)")
    ap.add_argument("--update-baselines", action="store_true", help="record the current version's hash and counts as the new baselines")
    ap.add_argument("--harness-timeout", type=int, default=7200, help="seconds")
    a = ap.parse_args()
    pick = lambda s: [x.strip() for x in s.split(",") if x.strip()] if s else []
    for n in pick(a.only) + pick(a.skip):
        if n not in STAGES:
            sys.exit("unknown stage %s (stages: %s)" % (n, ", ".join(STAGES)))
    if a.only:
        chosen = [s for s in STAGES if s in pick(a.only)]
    elif a.fast:
        chosen = list(FAST)
    else:
        chosen = [s for s in STAGES if s != "zip" or a.zip]
    if a.zip and "zip" not in chosen and not a.only:
        chosen.append("zip")
    chosen = [s for s in chosen if s not in pick(a.skip)]
    if not (0 < a.port_base < 65530 - 3):
        sys.exit("bad --port-base")

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    os.makedirs(WORK, exist_ok=True)
    ctx = {"stamp": stamp, "work": tempfile.mkdtemp(prefix=stamp + "-", dir=WORK), "port": a.port_base, "baselines": load_json(BASELINES, {}),
           "update": a.update_baselines, "smoke_only": a.fast, "harness_timeout": a.harness_timeout}
    stages = [Stage(s) for s in STAGES if s in chosen or True]
    by = {s.name: s for s in stages}
    for s in stages:
        if s.name not in chosen:
            s.reason = "not selected (--fast)" if a.fast else "not selected" if a.only or s.name != "zip" else "needs --zip"
            if s.name in pick(a.skip):
                s.reason = "--skip"
    say("gate: %s, stages %s, work dir %s" % (stamp, ",".join(chosen), ctx["work"]))
    t_all = time.time()
    try:
        for name in STAGES:
            s = by[name]
            if name not in chosen:
                continue
            say("[%s] running ..." % name)
            t0 = time.time()
            try:
                s.status, s.reason = FUNCS[name](s, ctx)
            except Exception as e:  # noqa: BLE001
                s.status, s.reason = FAIL, "gate error: %r" % (e,)
            s.secs = time.time() - t0
            say("[%s] %s in %s: %s" % (name, s.status, fmt(s.secs), s.reason))
    finally:
        child = ctx.get("child")
        if child and child.poll() is None:
            kill_tree(child.pid)
        total = time.time() - t_all
        text = report([by[n] for n in STAGES], total, stamp, sys.argv[1:])
        out = os.path.join(REPO, "review", "gate")
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, stamp + ".md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        shutil.copyfile(os.path.join(out, stamp + ".md"), os.path.join(out, "latest.md"))
        say("")
        say(text)
        say("report: " + os.path.join(out, stamp + ".md"))
        say("total: " + fmt(total))
        if not os.environ.get("GATE_KEEP_WORK"):
            shutil.rmtree(ctx["work"], ignore_errors=True)
    return 1 if any(s.status == FAIL for s in stages) else 0


if __name__ == "__main__":
    sys.exit(main())
