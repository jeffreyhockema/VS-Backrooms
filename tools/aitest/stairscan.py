"""Stairs headroom sweep: runs `/backrooms stairscan` over levels on a fresh world and prints the failing flights.

    python tools/aitest/stairscan.py --mods <Mods dir> --levels 1,4,5 [--sites 20] [--radius 40] [--seed 12345]
                                     [--port 43541] [--data <dir>] [--out <file>] [--at L:x:z[:r],...]

The probe walks the player's box (0.6 x 1.85, step 0.6) up every flight on the real collision boxes (see
src/Cheats/StairScan.cs). Output: the server's `[backrooms] stairscan` lines (a FAIL/PARTIAL line per flight, a per
kind line, a summary per level). Needs a build from `bash tools/locked.sh mod <tag>`. `--at 1:1200:-300:40` scans one
spot of a level instead of its arrival sites.
"""
import argparse
import os
import re
import shutil
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run  # noqa: E402


def scan(srv, command, timeout=900):
    """Sends the command until it stops reporting chunks loading; returns the stairscan lines."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        m = srv.mark()
        srv.cmd(command)
        got = srv.wait(lambda l: ("stairscan" in l and ("loading" in l or "stairscan:" in l and "sites" in l)) and l
                       or ("Found nowhere" in l or "There is no Level" in l) and l, m, 300)
        if got is None:
            raise RuntimeError("no answer to " + command)
        if "loading" in got:
            time.sleep(5)
            continue
        time.sleep(1)
        return [l for l in srv.since(m) if "[backrooms] stairscan" in l]
    raise RuntimeError("chunks never finished loading for " + command)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mods", required=True)
    ap.add_argument("--levels", default="")
    ap.add_argument("--sites", type=int, default=20)
    ap.add_argument("--radius", type=int, default=40)
    ap.add_argument("--seed", default="12345")
    ap.add_argument("--port", type=int, default=43541)
    ap.add_argument("--data", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--at", default="")
    a = ap.parse_args()

    data = a.data or tempfile.mkdtemp(prefix="stairscan-")
    run_cfg = "{ Port: %d, WorldConfig: { Seed: '%s', WorldType: 'backrooms', PlayStyle: 'backrooms' } }" % (a.port, a.seed)
    # (run.Server takes the seed from its own config string: build the same server with ours)
    import subprocess
    exe = run.Server.find_server()
    srv = run.Server.__new__(run.Server)
    srv.lines, srv.lock = [], __import__("threading").Lock()
    srv.ready = __import__("threading").Event()
    srv.p = subprocess.Popen([exe, "--dataPath", data, "--addModPath", a.mods.replace("\\", "/"), "--withconfig", run_cfg],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
    __import__("threading").Thread(target=srv.read, daemon=True).start()
    result = []
    try:
        if not srv.ready.wait(300):
            raise RuntimeError("server did not start")
        time.sleep(3)
        jobs = []
        for lv in [x for x in a.levels.split(",") if x]:
            jobs.append((lv, "/backrooms stairscan %s %d %d" % (lv, a.sites, a.radius)))
        for spec in [x for x in a.at.split(",") if x]:
            parts = spec.split(":")
            r = parts[3] if len(parts) > 3 else str(a.radius)
            jobs.append((parts[0], "/backrooms stairscan at %s %s %s" % (parts[1], parts[2], r)))
        for lv, cmd in jobs:
            t0 = time.time()
            lines = scan(srv, cmd)
            for l in lines:
                result.append(re.sub(r"^.*?\[backrooms\] stairscan ", "", l))
            print("\n".join(result[-len(lines):] if lines else []), flush=True)
            print("(%s took %.0f s)" % (cmd, time.time() - t0), flush=True)
    except BaseException:
        # (What the server said last, for a crash)
        for name in ("server-main.log", "server-event.log"):
            f = os.path.join(data, "Logs", name)
            if os.path.exists(f):
                print("--- tail of %s" % name)
                print("".join(open(f, encoding="utf-8", errors="replace").readlines()[-40:]))
        raise
    finally:
        srv.stop()
        if not a.data and not os.environ.get('STAIRSCAN_KEEP'):
            shutil.rmtree(data, ignore_errors=True)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write("\n".join(result) + "\n")


if __name__ == "__main__":
    main()
