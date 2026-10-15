"""Shoots a spot list in the real client, unattended, and makes a contact sheet of it.

    python tools/shotbot/batch.py --spots review/spots/level0.json [more.json ...] --build <mods dir> --out <dir>
                                  [--data <review data dir>] [--world gfxreview] [--seed 1672613597]
                                  [--format jpg|png] [--keep-open] [--only name,pattern*] [--dry-run]

What it does:
  1. Makes the isolated data dir (default %LOCALAPPDATA%/backrooms-gfxreview) if needed: the user's clientsettings.json
     copied from %APPDATA%/VintagestoryData with modPaths set to ["Mods"] only (the default list also loads the user's
     real Mods folder) and the view distance held at 256 so far terrain loads the same way every time.
  2. Makes the review world if the data dir has none: a dedicated server creates Saves/<world>.vcdbs with the fixed
     seed (the client's -o can only make worlds with a random seed), then stops.
  3. Copies the shotbot build (tools/shotbot/out/Mods/shotbot, from `dotnet build tools/shotbot`) beside the Backrooms
     build in the --build Mods dir.
  4. Writes commands.txt from the spot lists, launches
        Vintagestory.exe --dataPath <data> --addModPath <build> -o <world> -p backrooms
     with SHOTBOT_DIR set, and waits until the bot has taken the last shot (status.txt / marks.txt).
  5. Copies the shots to --out (one folder per spot list when there are several: --out/<list name>/), makes
     sheet.jpg in each, and closes the client (it sends /stop, which saves and stops the game's own server, then
     ends the process).

Spot lists are JSON: {"level": "0", "spots": [spot, ...]} or a bare list of spots. A spot:
    {"name": "wide-01",                       file name of the shot (unique within the list)
     "tp": [x, y, z],                         absolute feet position (/tp =x =y =z), or instead
     "nearest": "tent", "from": [x, y, z],    /backrooms nearest <target> searched from "from" (where to stand first)
     "look": [heading, pitch],                compass heading (0 N, 90 E), pitch in degrees (negative looks down)
     "fov": 70,                               optional, default 70
     "pre": ["/time set 12:00", "daylight"],   optional: lines starting with / are chat commands, others bot commands
     "inspection": true}                      optional: shot with the shotbot's daylight and a lantern in hand
Inspection spots get "daylight" and "/backrooms light lantern" (held in hotbar slot 9) on top of their own "pre";
the next ordinary spot turns daylight off and goes back to the empty slot 8 (slot 0 holds the folded note).

The bot yields when a human presses Escape three times in quick succession; batch.py then waits (it reports a stall
after --stall minutes without progress) rather than fighting the person at the keyboard.
"""
import argparse
import fnmatch
import glob
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
GAME = os.environ.get("VINTAGE_STORY", r"G:\Games\Vintagestory")
CLIENT = os.path.join(GAME, "Vintagestory.exe")
SERVER = os.path.join(GAME, "VintagestoryServer.exe")
DEFAULT_DATA = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "backrooms-gfxreview")
DEFAULT_SEED = "1672613597"
SHOTBOT_BUILD = os.path.join(HERE, "out", "Mods", "shotbot")
VIEW_DISTANCE = 256
DEFAULT_FOV = 70

HEADER = [
    "# header: wait for the world, then set the camera up the same way every time",
    "wait 4000",
    "closeguis",
    "focus",
    "hud off",
    "cmd /gm creative",
    "cmd /backrooms director off",
    "cmd /backrooms clear 128",
    # (B5) a Reality Shift that started in the review world never ends with the clock stopped (it runs in in-game
    # hours), and it blacks out every enclosed level: end one, and keep the player's stability full
    "cmd /backrooms shift 0",
    "cmd /backrooms stat stability 1",
    "cmd /time setmonth jun",
    "cmd /time set 12:00",
    "cmd /time stop",
    # (B7) setting the clock can jump the calendar a day or a month on, past the next Reality Shift's start: end it
    # again once the clock stands still (B7's second and third Level 4 runs came out black without this)
    "cmd /backrooms shift 0",
    "cmd /backrooms stat stability 1",
    "wait 2000",
    f"fov {DEFAULT_FOV}",
    "slot 8",
    "wait 1000",
]


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


# ---------------------------------------------------------------- setup

def ensure_data_dir(data):
    os.makedirs(os.path.join(data, "Saves"), exist_ok=True)
    dst = os.path.join(data, "clientsettings.json")
    if not os.path.exists(dst):
        src = os.path.join(os.environ["APPDATA"], "VintagestoryData", "clientsettings.json")
        shutil.copyfile(src, dst)
        log(f"copied {src}")
    with open(dst, encoding="utf-8-sig") as f:
        settings = json.load(f)
    changed = False
    lists = settings.setdefault("stringListSettings", {})
    if lists.get("modPaths") != ["Mods"]:
        lists["modPaths"] = ["Mods"]
        changed = True
    ints = settings.setdefault("intSettings", {})
    if ints.get("viewDistance") != VIEW_DISTANCE:
        ints["viewDistance"] = VIEW_DISTANCE
        changed = True
    if changed:
        with open(dst, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        log("clientsettings.json: modPaths [\"Mods\"], viewDistance %d" % VIEW_DISTANCE)


def ensure_world(data, world, mods, seed):
    save = os.path.join(data, "Saves", world + ".vcdbs")
    if os.path.exists(save):
        return save
    log(f"creating world {world} with seed {seed} (dedicated server)")
    srv = os.path.join(data, "_server")
    shutil.rmtree(srv, ignore_errors=True)
    os.makedirs(srv)
    config = "{ WorldConfig: { Seed: '%s', WorldType: 'backrooms', PlayStyle: 'backrooms', WorldName: '%s', " \
             "SaveFileLocation: '%s', MapSizeY: 256 } }" % (seed, world, save.replace("\\", "/"))
    # Only the Backrooms build: the shotbot is client-side
    only = os.path.join(srv, "Mods")
    os.makedirs(only)
    shutil.copytree(os.path.join(mods, "backroomsss"), os.path.join(only, "backroomsss"))
    out = open(os.path.join(srv, "out.txt"), "w", encoding="utf-8")
    p = subprocess.Popen([SERVER, "--dataPath", srv, "--addModPath", only, "--withconfig", config],
                         stdin=subprocess.PIPE, stdout=out, stderr=subprocess.STDOUT)
    logf = os.path.join(srv, "Logs", "server-main.log")
    t0 = time.time()
    while time.time() - t0 < 600:
        time.sleep(3)
        if p.poll() is not None:
            break
        try:
            if "Dedicated Server now running" in open(logf, encoding="utf-8", errors="replace").read():
                time.sleep(5)
                p.stdin.write(b"/stop\r\n")  # the console wants CRLF
                p.stdin.flush()
                break
        except OSError:
            pass
    p.wait(timeout=300)
    out.close()
    if not os.path.exists(save):
        sys.exit(f"world creation failed: see {srv}")
    log(f"world created: {save}")
    return save


def ensure_shotbot(mods):
    src = SHOTBOT_BUILD
    if not os.path.exists(os.path.join(src, "shotbot.dll")):
        sys.exit("no shotbot build: run  %LOCALAPPDATA%/Microsoft/dotnet/dotnet.exe build tools/shotbot")
    dst = os.path.join(mods, "shotbot")
    os.makedirs(dst, exist_ok=True)
    for f in os.listdir(src):
        s, d = os.path.join(src, f), os.path.join(dst, f)
        if not os.path.exists(d) or os.path.getmtime(s) > os.path.getmtime(d):
            shutil.copy2(s, d)


# ---------------------------------------------------------------- spot lists

def load_spots(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    spots = data["spots"] if isinstance(data, dict) else data
    name = os.path.splitext(os.path.basename(path))[0]
    return name, spots


def fmt(v):
    return ("%.2f" % v).rstrip("0").rstrip(".")


def spot_commands(spot, prefix, state):
    """The bot lines for one spot. state carries daylight / held-light across spots."""
    out = [f"# spot {prefix}{spot['name']}"]
    inspection = bool(spot.get("inspection"))
    if not inspection and state.get("daylight"):
        out += ["daylight off", "slot 8"]
        state["daylight"] = False
    pre = list(spot.get("pre", []))
    if inspection:
        out.append("slot 9")
        pre = ["daylight", "/backrooms light lantern"] + [p for p in pre if p not in ("daylight", "/backrooms light lantern")]
        state["daylight"] = True
    elif "daylight" in pre:
        state["daylight"] = True  # (an ordinary day spot: the next spot without it turns daylight off again)
    for p in pre:
        out.append(("cmd " + p) if p.startswith("/") else p)
    if "nearest" in spot:
        fx, fy, fz = spot["from"]
        out += [f"tp {fmt(fx)} {fmt(fy)} {fmt(fz)}", "ready 48",
                f"cmd /backrooms nearest {spot['nearest']}", "waitchat 60000", "wait 1500"]
    else:
        x, y, z = spot["tp"]
        out.append(f"tp {fmt(x)} {fmt(y)} {fmt(z)}")
    out.append("ready 48")
    h, p = spot.get("look", [0, 0])
    out.append(f"look {fmt(h)} {fmt(p)}")
    fov = spot.get("fov", DEFAULT_FOV)
    if fov != state.get("fov", DEFAULT_FOV):
        out.append(f"fov {fov}")
        state["fov"] = fov
    out += ["wait 700", f"look {fmt(h)} {fmt(p)}", f"shot {prefix}{spot['name']}"]
    return out


def build_commands(lists, only=None):
    lines = list(HEADER)
    state = {}
    shots = []  # (list name, shot file stem, spot name)
    multi = len(lists) > 1
    for name, spots in lists:
        lines.append(f"# ===== {name}")
        prefix = f"{name}__" if multi else ""
        # inspection shots last, so the daylight and the lantern never leak into the ordinary ones
        ordered = [s for s in spots if not s.get("inspection")] + [s for s in spots if s.get("inspection")]
        for s in ordered:
            if only and not any(fnmatch.fnmatchcase(s["name"], pat) for pat in only):
                continue
            lines += spot_commands(s, prefix, state)
            shots.append((name, prefix + s["name"], s["name"]))
    lines += ["daylight off", "wait 3000", "mark __end__"]
    return lines, shots


# ---------------------------------------------------------------- running the client

def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def status_done(botdir):
    for line in read(os.path.join(botdir, "status.txt")).splitlines():
        if line.startswith("done "):
            return int(line.split()[1])
    return -1


def run_client(lines, data, mods, world, botdir, keep_open=False, stall_minutes=6, timeout_minutes=240, extra_wait=None):
    """Writes commands.txt, launches the client and waits for 'mark __end__'. Returns the client process."""
    if os.path.exists(botdir):
        for f in glob.glob(os.path.join(botdir, "*")):
            if os.path.isfile(f):
                os.remove(f)
    os.makedirs(botdir, exist_ok=True)
    with open(os.path.join(botdir, "commands.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    env = dict(os.environ, SHOTBOT_DIR=botdir)
    args = [CLIENT, "--dataPath", data, "--addModPath", mods, "-o", world, "-p", "backrooms"]
    log("launching: " + " ".join(args))
    proc = subprocess.Popen(args, env=env, cwd=GAME, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    last_done, last_change = -1, time.time()
    warned = False
    total = len(lines)
    while True:
        time.sleep(5)
        if proc.poll() is not None:
            log(f"the client exited (code {proc.returncode}) before the end; see {botdir}/log.txt")
            return proc, False
        if "__end__" in read(os.path.join(botdir, "marks.txt")):
            log("all commands done")
            return proc, True
        done = status_done(botdir)
        if done != last_done:
            if done >= 0 and (done // 50) != (last_done // 50):
                log(f"progress: {done}/{total} commands")
            last_done, last_change = done, time.time()
            warned = False
        elif time.time() - last_change > stall_minutes * 60 and not warned:
            yielded = "leaving it alone" in read(os.path.join(botdir, "log.txt"))
            log(f"no progress for {stall_minutes} min at command {done}/{total}"
                + (" (the bot yielded to someone pressing Escape; waiting)" if yielded else "; still waiting"))
            warned = True
        if time.time() - t0 > timeout_minutes * 60:
            log("timed out")
            return proc, False


def close_client(proc, botdir):
    """Stops the game's own server (it saves the world) with /stop, then ends the client."""
    if proc.poll() is not None:
        return
    with open(os.path.join(botdir, "commands.txt"), "a", encoding="utf-8") as f:
        f.write("cmd /stop\nwait 4000\n")
    for _ in range(12):
        time.sleep(2)
        if proc.poll() is not None:
            return
    subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        pass
    log("client closed")


# ---------------------------------------------------------------- output

def save_shot(src, dst_stem, fmt_):
    from PIL import Image
    if fmt_ == "png":
        shutil.copyfile(src, dst_stem + ".png")
        return dst_stem + ".png"
    Image.open(src).convert("RGB").save(dst_stem + ".jpg", quality=90)
    return dst_stem + ".jpg"


def make_sheet(folder, names, out, cols=3, w=640, h=360):
    """A contact sheet of the shots in folder, in the order given, with their names."""
    from PIL import Image, ImageDraw
    files = []
    for n in names:
        p = next((os.path.join(folder, n + e) for e in (".jpg", ".png") if os.path.exists(os.path.join(folder, n + e))), None)
        files.append((n, p))
    if not files:
        return None
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (w * cols, (h + 20) * rows), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    for i, (n, p) in enumerate(files):
        x, y = (i % cols) * w, (i // cols) * (h + 20)
        if p:
            sheet.paste(Image.open(p).convert("RGB").resize((w, h), Image.LANCZOS), (x, y + 20))
        else:
            d.rectangle((x, y + 20, x + w - 1, y + 20 + h - 1), outline=(255, 0, 255))
            d.text((x + 8, y + 30), "MISSING", fill=(255, 0, 255))
        d.text((x + 4, y + 4), n, fill=(255, 255, 255))
    sheet.save(out, quality=88)
    return out


def collect(lists, shots, botdir, out, fmt_):
    multi = len(lists) > 1
    missing = []
    for name, spots in lists:
        dest = os.path.join(out, name) if multi else out
        os.makedirs(dest, exist_ok=True)
        names = []
        for lname, stem, sname in shots:
            if lname != name:
                continue
            src = os.path.join(botdir, stem + ".png")
            if os.path.exists(src):
                save_shot(src, os.path.join(dest, sname), fmt_)
            else:
                missing.append(stem)
            names.append(sname)
        # the sheet shows the whole list (shots from an earlier run included, when --only took a few again)
        every = [x["name"] for x in spots if not x.get("inspection")] + [x["name"] for x in spots if x.get("inspection")]
        sheet = make_sheet(dest, every, os.path.join(dest, "sheet.jpg"))
        log(f"{name}: {len(names)} shot -> {dest}" + (f", sheet {sheet}" if sheet else ""))
    if missing:
        log(f"MISSING {len(missing)} shots: " + ", ".join(missing))
    return missing


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--spots", nargs="+", required=True)
    ap.add_argument("--build", required=True, help="the Mods dir holding backroomsss/ (tools/locked.sh mod <tag>)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--data", default=DEFAULT_DATA)
    ap.add_argument("--world", default="gfxreview")
    ap.add_argument("--seed", default=DEFAULT_SEED, help="only used when the world has to be created")
    ap.add_argument("--format", default="jpg", choices=("jpg", "png"))
    ap.add_argument("--only", default="", help="comma-separated spot names or patterns to shoot (e.g. '*-wide,*-close')")
    ap.add_argument("--keep-open", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="write commands.txt only")
    ap.add_argument("--stall", type=int, default=6, help="minutes without progress before reporting a stall")
    a = ap.parse_args()

    data, mods = os.path.abspath(a.data), os.path.abspath(a.build)
    lists = [load_spots(p) for p in a.spots]
    only = set(a.only.split(",")) if a.only else None
    lines, shots = build_commands(lists, only)
    botdir = os.path.join(data, "shotbot-run")
    if a.dry_run:
        os.makedirs(botdir, exist_ok=True)
        with open(os.path.join(botdir, "commands.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        log(f"{len(shots)} shots, {len(lines)} commands -> {botdir}/commands.txt")
        return
    if not os.path.exists(os.path.join(mods, "backroomsss")):
        sys.exit(f"no backroomsss build in {mods}")
    ensure_data_dir(data)
    ensure_world(data, a.world, mods, a.seed)
    ensure_shotbot(mods)
    log(f"{len(shots)} shots, {len(lines)} commands")
    proc, ok = run_client(lines, data, mods, a.world, botdir, stall_minutes=a.stall)
    seed = read(os.path.join(botdir, "ready.txt")).strip().replace("\n", ", ")
    log("world: " + seed)
    missing = collect(lists, shots, botdir, os.path.abspath(a.out), a.format)
    if not a.keep_open:
        close_client(proc, botdir)
    sys.exit(0 if ok and not missing else 1)


if __name__ == "__main__":
    main()
