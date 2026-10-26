"""Client test rig: runs the real game client against a dedicated test server, off-screen, from a scenario file.

    python tools/clientrig/rig.py --mods <Mods dir with backroomsss> --scenario tools/clientrig/scenarios/boot.yaml
                                  [--seed 424242] [--port 42797] [--out review/clientrig/<date>] [--keep-open] [--dry-run]

See docs/DEVELOPING.md, section "Client rig". The steps of a scenario (a YAML or JSON list):

    bot: <shotbot line>                 any shotbot command (cmd /backrooms ..., tp, look, ready, wait, shot, ...)
    cmd: /backrooms menace              a chat line from the client, then wait for its reply (shorthand for bot cmd + waitchat)
    server: <console line>              a line on the server console (/backrooms commands run as the server; /time ...)
    face: megplacard                    /backrooms rig face <text> and turn the camera to what it finds
    expect_chat: <text>  [timeout=N]    a chat line (tags stripped, case ignored) containing text arrives; N seconds, default 15
    expect_log: <text>   [timeout=N]    a line of the server log or the client log contains text
    expect_no_startup_issues:           the client log has no "Captured N issues during startup"
    expect_no_log: <text>               no line of the server or client log contains text
    expect_shot: <name>                 SHOTBOT_DIR/<name>.png exists and is bigger than 20 KB
    expect_telemetry: <ev>              a JSON Lines event with "ev": <ev> is in the server data dir (skipped if there is no telemetry)
    shot: <name>                        screenshot (a bot shot, with a pause for the frame to settle)
    sleep: <ms>                         wait
    note: <text>                        a line in the report
Any step may instead be a mapping: {expect_chat: "text", timeout: 70}. Each step passes or fails; the run continues.
"""
import argparse
import ctypes
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from ctypes import wintypes

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "tools", "shotbot"))
import batch  # noqa: E402  (make_sheet, save_shot, the game paths)

GAME = batch.GAME
CLIENT, SERVER = batch.CLIENT, batch.SERVER
RIG_ROOT = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "backrooms-clientrig")
MUTED = ("masterSoundLevel", "soundLevel", "entitySoundLevel", "ambientSoundLevel", "weatherSoundLevel", "musicLevel")


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""



TAGS = re.compile(r"<[^>]+>")


def clean(s):
    return TAGS.sub("", s).replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")


# ---------------------------------------------------------------- windows

user32 = ctypes.windll.user32
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.IsIconic.argtypes = [wintypes.HWND]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetShellWindow.restype = wintypes.HWND
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
ENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
SWP_NOZORDER, SWP_NOACTIVATE, SW_SHOWNOACTIVATE = 0x4, 0x10, 4


def windows_of(pid):
    """(hwnd, title) of the visible top-level windows of a process."""
    found = []

    def cb(hwnd, _):
        p = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid and user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, buf, n + 1)
            found.append((hwnd, buf.value))
        return True

    user32.EnumWindows(ENUMPROC(cb), 0)
    return found


def move_offscreen(pid, timeout=20):
    """HARD RULE: call this only once the world is in (the level has finalized, ready.txt exists), always with SWP_NOACTIVATE, and
    follow it with the focus handed to the shell. A move during the loading screen crashed a client (vanilla shader error,
    2026-10-25), and a window left on-screen takes the user's keyboard. Never minimize the window.
    Moves the client's window to x = -4000 without activating it, restores it if minimized, hands focus to the shell.
    """
    t0 = time.time()
    while time.time() - t0 < timeout:
        wins = windows_of(pid)
        if wins:
            hwnd = max(wins, key=lambda w: len(w[1]))[0]
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
            user32.SetWindowPos(hwnd, 0, -4000, 200, 1600, 900, SWP_NOZORDER | SWP_NOACTIVATE)
            user32.SetForegroundWindow(user32.GetShellWindow())
            time.sleep(0.5)
            r = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(r))
            iconic = bool(user32.IsIconic(hwnd))
            log(f"window moved off-screen: left {r.left}, iconic {iconic}")
            return (r.left < -1000) and not iconic
        time.sleep(0.5)
    return False


def kill_tree(pid):
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)


# ---------------------------------------------------------------- server

class Server:
    def __init__(self, mods, data, port, seed):
        self.lines, self.lock, self.ready = [], threading.Lock(), threading.Event()
        cfg = "{ Port: %d, WorldConfig: { Seed: '%s', WorldType: 'backrooms', PlayStyle: 'backrooms' } }" % (port, seed)
        self.out = open(os.path.join(data, "console.txt"), "w", encoding="utf-8")
        self.p = subprocess.Popen([SERVER, "--dataPath", data, "--addModPath", mods, "--withconfig", cfg], cwd=GAME,
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for raw in iter(self.p.stdout.readline, b""):
            s = raw.decode("utf-8", "replace").rstrip()
            with self.lock:
                self.lines.append(s)
            self.out.write(s + "\n")
            self.out.flush()
            if "Dedicated Server now running" in s:
                self.ready.set()

    def cmd(self, c):
        with self.lock:
            self.lines.append(">>> " + c)
        self.p.stdin.write((c + "\r\n").encode("utf-8"))
        self.p.stdin.flush()

    def text(self):
        with self.lock:
            return "\n".join(self.lines)

    def stop(self):
        try:
            self.cmd("/stop")
            self.p.wait(120)
        except Exception:  # noqa: BLE001
            kill_tree(self.p.pid)


# ---------------------------------------------------------------- setup

def prepare_client_data(data):
    os.makedirs(data, exist_ok=True)
    shutil.rmtree(os.path.join(data, "Logs"), ignore_errors=True)
    src = os.path.join(os.environ.get("APPDATA", ""), "VintagestoryData", "clientsettings.json")
    if not os.path.exists(src):
        sys.exit(f"no clientsettings.json at {src}; run the game once")
    with open(src, encoding="utf-8-sig") as f:
        s = json.load(f)
    s.setdefault("stringListSettings", {})["modPaths"] = ["Mods"]
    ints = s.setdefault("intSettings", {})
    ints["viewDistance"] = 128
    for k in MUTED:
        ints[k] = 0
    with open(os.path.join(data, "clientsettings.json"), "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)


def prepare_mods(mods, root):
    """The client's mods dir gets the shotbot beside the Backrooms build. The server gets a dir with the Backrooms build only."""
    if not os.path.exists(os.path.join(mods, "backroomsss")):
        sys.exit(f"no backroomsss build in {mods}")
    if not os.path.exists(os.path.join(batch.SHOTBOT_BUILD, "shotbot.dll")):
        log("building the shotbot")
        dn = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "dotnet", "dotnet.exe")
        subprocess.run([dn, "build", os.path.join(REPO, "tools", "shotbot"), "-nologo", "-clp:NoSummary"], check=True)
    batch.ensure_shotbot(mods)
    smods = os.path.join(root, "servermods")
    shutil.rmtree(smods, ignore_errors=True)
    shutil.copytree(os.path.join(mods, "backroomsss"), os.path.join(smods, "backroomsss"))
    return smods


# ---------------------------------------------------------------- the run

class Run:
    def __init__(self, a):
        self.a = a
        self.root = os.path.join(RIG_ROOT, "run")
        self.botdir = os.path.join(self.root, "bot")
        self.sdata = os.path.join(self.root, "server")
        self.cdata = os.path.join(self.root, "client")
        self.steps = []
        self.notes = []
        self.marks = 0
        self.chat_off = 0
        self.player = None
        self.srv = self.client = None
        self.crash = None

    # -- bot
    def bot(self, line, timeout=90):
        """Appends a line (and a mark behind it); waits until the bot has done both."""
        self.marks += 1
        tag = f"__s{self.marks}__"
        with open(os.path.join(self.botdir, "commands.txt"), "a", encoding="utf-8") as f:
            f.write(line + "\nmark " + tag + "\n")
        end = time.time() + timeout
        while time.time() < end:
            if tag in read(os.path.join(self.botdir, "marks.txt")):
                return True
            if self.client.poll() is not None:
                self.crash = self.crash or f"the client exited (code {self.client.returncode}) during: {line}"
                return False
            time.sleep(0.3)
        return False

    def chat_text(self):
        return read(os.path.join(self.botdir, "chat.txt"))

    def chat_since(self):
        # (the bot's own "#mark" lines are not chat)
        return chr(10).join(l for l in clean(self.chat_text()[self.chat_off:]).splitlines() if not l.startswith("#mark"))

    def mark_chat(self):
        self.chat_off = len(self.chat_text())

    def client_log(self):
        return read(os.path.join(self.cdata, "Logs", "client-main.log"))

    def server_log(self):
        return read(os.path.join(self.sdata, "Logs", "server-main.log")) + "\n" + self.srv.text()

    # -- start up
    def start(self):
        a = self.a
        shutil.rmtree(self.root, ignore_errors=True)
        for d in (self.botdir, self.sdata):
            os.makedirs(d)
        prepare_client_data(self.cdata)
        smods = prepare_mods(a.mods, self.root)
        log("starting the server")
        self.srv = Server(smods, self.sdata, a.port, a.seed)
        if not self.srv.ready.wait(600):
            raise RuntimeError("the server did not come up in 10 minutes; see " + os.path.join(self.sdata, "console.txt"))
        log("server ready")
        env = dict(os.environ, SHOTBOT_DIR=self.botdir)
        args = [CLIENT, "--dataPath", self.cdata, "--addModPath", a.mods, "-c", f"localhost:{a.port}"]
        log("starting the client (its window takes focus once; it is moved off-screen when the world has loaded)")
        self.client = subprocess.Popen(args, env=env, cwd=GAME, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # in the world = the bot has written ready.txt (the level finalized; status.txt only appears after its first command)
        t0 = time.time()
        while time.time() - t0 < 300:
            if self.client.poll() is not None:
                raise RuntimeError(f"the client exited (code {self.client.returncode}) before the world loaded; {self.crash_info()}")
            if os.path.exists(os.path.join(self.botdir, "ready.txt")):
                break
            if self.crash_info():
                raise RuntimeError("the client crashed while loading; " + self.crash)
            time.sleep(1)
        else:
            raise RuntimeError("the client did not reach the world in 5 minutes")
        log("the client is in the world")
        time.sleep(6)
        if not move_offscreen(self.client.pid):
            self.notes.append("WARNING: the window could not be confirmed off-screen and not minimized")
        self.find_player()
        if self.player:
            self.srv.cmd("/op " + self.player)
            time.sleep(1.5)
        else:
            self.notes.append("WARNING: no player name found in the server log; /op not sent")
        self.bot("closeguis")
        self.mark_chat()

    def crash_info(self):
        for p in glob.glob(os.path.join(self.cdata, "Logs", "*crash*")):
            self.crash = self.crash or "client crash log: " + p
            return self.crash
        return None

    def find_player(self):
        text = self.server_log()
        for pat in (r"identification\. Name: (\S+)", r"(\S+) \[[^\]]*\] joins", r"(\S+) joins", r"Player (\S+) joined", r"(\S+) \[[^\]]*\] .*?joined"):
            m = re.search(pat, text)
            if m:
                self.player = m.group(1)
                log("player " + self.player)
                return

    # -- steps
    def run_step(self, n, step):
        items = dict(step)
        timeout = items.pop("timeout", None)
        kind, text = next(iter(items.items()))
        text = "" if text is None else str(text)
        m = re.search(r"\s+timeout=(\d+)\s*$", text)
        if m:
            timeout = int(m.group(1))
            text = text[:m.start()]
        t0 = time.time()
        try:
            ok, detail = self.do(kind, text, timeout)
        except Exception as e:  # noqa: BLE001
            ok, detail = False, "error: %r" % e
        self.steps.append(dict(n=n, kind=kind, text=text, ok=ok, detail=detail, secs=time.time() - t0))
        log(f"step {n} {kind}: {text}  ->  {'ok' if ok else 'FAIL'} {detail}")

    def do(self, kind, text, timeout):
        if self.client.poll() is not None:
            return False, "the client is not running"
        if kind == "bot":
            if text.startswith("cmd"):
                self.mark_chat()
            return self.bot(text, timeout or 90), ""
        if kind == "cmd":
            self.mark_chat()
            ok = self.bot("cmd " + text, 30)
            self.bot("waitchat " + str((timeout or 15) * 1000), 40 + (timeout or 15))
            return ok, "reply: " + " | ".join(self.chat_since().strip().splitlines()[:3])[:300]
        if kind == "server":
            self.srv.cmd(text)
            time.sleep(1.0)
            return True, ""
        if kind == "face":
            self.mark_chat()
            self.bot("cmd /backrooms rig face " + text, 30)
            self.bot("waitchat 10000", 30)
            m = re.search(r"rig-face (\S+) at (-?\d+) (-?\d+) (-?\d+) dist ([\d.]+) look (-?\d+) (-?\d+)", self.chat_since())
            if not m:
                return False, "not found: " + self.chat_since().strip()[:200]
            self.bot(f"look {m.group(6)} {m.group(7)}")
            return True, f"{m.group(1)} at {m.group(2)} {m.group(3)} {m.group(4)}, {m.group(5)} blocks, look {m.group(6)} {m.group(7)}"
        if kind == "expect_chat":
            needle = text.lower()
            end = time.time() + (timeout or 15)
            while time.time() < end:
                for line in self.chat_since().splitlines():
                    if needle in line.lower():
                        self.chat_off = len(self.chat_text())
                        return True, line.strip()[:200]
                if self.client.poll() is not None:
                    return False, "the client exited"
                time.sleep(0.5)
            return False, "no such chat line; chat was: " + " | ".join(self.chat_since().strip().splitlines()[-4:])[:300]
        if kind == "expect_log":
            needle = text.lower()
            end = time.time() + (timeout or 15)
            while True:
                for name, body in (("server", self.server_log()), ("client", self.client_log())):
                    for line in body.splitlines():
                        if needle in line.lower() and not line.startswith(">>>"):
                            return True, f"{name}: {line.strip()[:200]}"
                if time.time() > end:
                    return False, "not in the server or client log"
                time.sleep(1)
        if kind == "expect_no_startup_issues":
            issues = self.startup_issues()
            if not issues:
                return True, "0 captured issues"
            first = next((r.strip() for r in issues[0][1] if "Exception" in r or "Error" in r), "")
            return False, f"Captured {issues[0][0]} issues during startup; first: {first[:200]}"
        if kind == "expect_no_log":
            needle = text.lower()
            for name, body in (("server", self.server_log()), ("client", self.client_log())):
                for line in body.splitlines():
                    if needle in line.lower() and not line.startswith(">>>"):
                        return False, f"{name}: {line.strip()[:200]}"
            return True, ""
        if kind in ("expect_shot", "shot"):
            if kind == "shot":
                self.bot("wait 700")
                if not self.bot("shot " + text, 60):
                    return False, "the bot did not finish the shot"
                time.sleep(0.5)
            p = os.path.join(self.botdir, text + ".png")
            size = os.path.getsize(p) if os.path.exists(p) else 0
            return size > 20 * 1024, f"{size // 1024} KB"
        if kind == "expect_telemetry":
            files = glob.glob(os.path.join(self.sdata, "**", "*.jsonl"), recursive=True)
            if not files:
                return True, "SKIPPED: no telemetry (*.jsonl) in the server data dir; the branch is not in this build"
            end = time.time() + (timeout or 10)
            while time.time() < end:
                for f in files:
                    for line in read(f).splitlines():
                        if re.search(r'"ev"\s*:\s*"%s"' % re.escape(text), line):
                            return True, line[:200]
                time.sleep(1)
            return False, "no such event in " + ", ".join(os.path.basename(f) for f in files)
        if kind == "sleep":
            time.sleep(float(text) / 1000)
            return True, ""
        if kind == "note":
            self.notes.append(text)
            return True, ""
        return False, "unknown step kind " + kind

    # -- end
    def finish(self, keep_open):
        if keep_open:
            log("--keep-open: leaving the client and server running (client pid %s, server pid %s)"
                % (self.client and self.client.pid, self.srv and self.srv.p.pid))
            return
        if self.client and self.client.poll() is None:
            kill_tree(self.client.pid)
        if self.srv and self.srv.p.poll() is None:
            self.srv.stop()
            if self.srv.p.poll() is None:
                kill_tree(self.srv.p.pid)

    def startup_issues(self):
        lines = self.client_log().splitlines()
        out = []
        for i, line in enumerate(lines):
            m = re.search(r"Captured (\d+) issues? during startup", line)
            if m:
                rest = lines[i + 1:i + 41]
                end = next((k for k, r in enumerate(rest) if "=====" in r), len(rest))
                out.append((int(m.group(1)), rest[:end]))
        return out

    @staticmethod
    def error_lines(text, limit=60):
        out = []
        for line in text.splitlines():
            if re.search(r"\[(Error|Fatal)\]|Exception", line) and "Captured" not in line:
                out.append(line.strip()[:300])
        return out[:limit]


def load_scenario(path):
    with open(path, encoding="utf-8") as f:
        body = f.read()
    if path.lower().endswith((".yaml", ".yml")):
        import yaml
        data = yaml.safe_load(body)
    else:
        data = json.loads(body)
    meta = {}
    if isinstance(data, dict):
        meta, data = data, data.get("steps", [])
    steps = []
    for s in data:
        if isinstance(s, str):
            k, _, v = s.partition(":")
            s = {k.strip(): v.strip()}
        steps.append(s)
    return meta, steps


KINDS = {"bot", "cmd", "server", "face", "expect_chat", "expect_log", "expect_no_log", "expect_no_startup_issues", "expect_shot",
         "expect_telemetry", "shot", "sleep", "note"}
NEEDS_TEXT = KINDS - {"expect_no_startup_issues", "note"}


def validate(steps):
    """Problems in a scenario, without launching anything."""
    problems, shots = [], set()
    for n, st in enumerate(steps, 1):
        if not isinstance(st, dict):
            problems.append(f"step {n}: not a mapping: {st!r}")
            continue
        extra = [k for k in st if k != "timeout"]
        if len(extra) != 1:
            problems.append(f"step {n}: needs exactly one step key, has {extra}")
            continue
        kind, text = extra[0], st[extra[0]]
        text = "" if text is None else str(text).strip()
        if kind not in KINDS:
            problems.append(f"step {n}: unknown step kind {kind!r}")
            continue
        if kind in NEEDS_TEXT and not text:
            problems.append(f"step {n}: {kind} needs a value")
        if kind == "sleep" and not re.fullmatch(r"\d+(\.\d+)?", text):
            problems.append(f"step {n}: sleep wants milliseconds")
        if kind in ("cmd", "server") and not text.startswith("/"):
            problems.append(f"step {n}: {kind} line should start with /: {text!r}")
        if kind == "shot":
            shots.add(re.sub(r"\s+timeout=\d+$", "", text))
        if kind == "expect_shot" and re.sub(r"\s+timeout=\d+$", "", text) not in shots:
            problems.append(f"step {n}: expect_shot {text!r} has no earlier shot step")
    return problems


def write_report(run, meta, name, out, boot_error):
    os.makedirs(out, exist_ok=True)
    shots = []
    for s in run.steps:
        if s["kind"] in ("shot", "expect_shot"):
            src = os.path.join(run.botdir, s["text"] + ".png")
            if os.path.exists(src):
                batch.save_shot(src, os.path.join(out, s["text"]), "png")
                if s["text"] not in shots:
                    shots.append(s["text"])
    sheet = batch.make_sheet(out, shots, os.path.join(out, "sheet.jpg")) if shots else None
    chat = os.path.join(run.botdir, "chat.txt")
    if os.path.exists(chat):
        shutil.copyfile(chat, os.path.join(out, "chat.txt"))
    clog, slog = run.client_log(), run.server_log()
    with open(os.path.join(out, "client-main.log"), "w", encoding="utf-8") as f:
        f.write(clog)
    with open(os.path.join(out, "server.log"), "w", encoding="utf-8") as f:
        f.write(slog)
    failed = [s for s in run.steps if not s["ok"]]
    issues = run.startup_issues()
    lines = [f"# Client rig: {name}", "", str(meta.get("description", "")), "",
             f"Run {time.strftime('%Y-%m-%d %H:%M:%S')}, build `{run.a.mods}`, seed {run.a.seed}, port {run.a.port}, player {run.player}.", ""]
    if boot_error:
        lines += ["## Did not run", "", boot_error, ""]
    if run.crash:
        lines += ["## CRASH", "", run.crash, "", "The Vintage Story crash reporter window may still be open on the desktop.", ""]
    lines += [f"## Steps: {len(run.steps) - len(failed)} passed, {len(failed)} failed", "",
              "| # | step | result | secs | detail |", "|---|---|---|---|---|"]
    for s in run.steps:
        d = s["detail"].replace("|", "/").replace("\n", " ")
        lines.append(f"| {s['n']} | `{s['kind']}: {s['text']}` | {'ok' if s['ok'] else '**FAIL**'} | {s['secs']:.1f} | {d} |")
    lines += ["", "## Client startup issues", ""]
    if not issues:
        lines.append("None captured (no \"Captured N issues during startup\" line in client-main.log).")
    for n, rest in issues:
        lines += [f"**Captured {n} issues during startup.** The log after it:", "", "```"] + [r[:260] for r in rest] + ["```", ""]
    errs = run.error_lines(slog)
    lines += ["", "## Server error lines", ""] + ((["```"] + errs + ["```"]) if errs else ["None."])
    cerrs = run.error_lines(clog)
    lines += ["", "## Client error lines", ""] + ((["```"] + cerrs + ["```"]) if cerrs else ["None."])
    if run.notes:
        lines += ["", "## Notes", ""] + [f"- {n}" for n in run.notes]
    if sheet:
        lines += ["", "## Screenshots", "", "![sheet](sheet.jpg)", ""] + [f"- {s}" for s in shots]
    lines += ["", "## Chat log", "", "```"] + [clean(x) for x in run.chat_text().splitlines()][-200:] + ["```", ""]
    with open(os.path.join(out, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return failed, issues


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mods", default=None, help="the Mods dir holding backroomsss/ (tools/locked.sh mod <tag>)")
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--seed", default="424242")
    ap.add_argument("--port", type=int, default=42797)
    ap.add_argument("--out", default=None)
    ap.add_argument("--keep-open", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="validate the scenario and print its steps; launches nothing")
    a = ap.parse_args()
    meta, steps = load_scenario(a.scenario)
    problems = validate(steps)
    if a.dry_run:
        for n, st in enumerate(steps, 1):
            print(n, st)
        for p in problems:
            print("PROBLEM:", p)
        if a.mods and not os.path.exists(os.path.join(a.mods, "backroomsss")):
            print(f"PROBLEM: no backroomsss build in {a.mods}")
            problems.append("mods")
        print("scenario ok" if not problems else f"{len(problems)} problem(s)")
        sys.exit(1 if problems else 0)
    if not a.mods:
        sys.exit("--mods is required")
    if problems:
        sys.exit("scenario problems:\n  " + "\n  ".join(problems))
    a.mods = os.path.abspath(a.mods)
    name = os.path.splitext(os.path.basename(a.scenario))[0]
    base = a.out or os.path.join(REPO, "review", "clientrig", time.strftime("%Y-%m-%d"))
    out = os.path.join(os.path.abspath(base), name)
    run = Run(a)
    boot_error = None
    failed = []
    try:
        run.start()
        for n, step in enumerate(steps, 1):
            run.run_step(n, step)
        time.sleep(1)
    except Exception as e:  # noqa: BLE001
        boot_error = repr(e)
        log("FAILED: " + boot_error)
    finally:
        try:
            failed, _ = write_report(run, meta, name, out, boot_error)
        except Exception as e:  # noqa: BLE001
            log("report failed: %r" % e)
            failed = [1]
        run.finish(a.keep_open)
    log(f"report: {os.path.join(out, 'report.md')}")
    sys.exit(1 if (failed or boot_error or run.crash) else 0)


if __name__ == "__main__":
    main()
