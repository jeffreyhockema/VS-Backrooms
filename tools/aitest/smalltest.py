"""Headless checks of the 2026-11 feedback round's small package (butter, borax, vanilla drinks, rot).

    python tools/aitest/smalltest.py --mods "$TEMP/backrooms-build/build-fbsmall/Mods" --port 43280 [--layout 16] [--washers 400]

Starts a dedicated server on a fresh world (layout version --layout, default the current one) and prints:
- the average drops of the icebox, washer, dryer, torn supply box and emptied crate over many rolls (`/backrooms classdrops`);
- Level 8's ore round some spots (`/backrooms smalltest ore`): borax in a version 16 world, none (vanilla's only) in a version 15 one;
- a bowl or jug of each vanilla liquid drunk through the game's own code by a straw dummy (`/backrooms smalltest sip`).
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run  # noqa: E402


class LayoutServer(run.Server):
    def __init__(self, mods, data, port, layout):
        import threading
        self.lines = []
        self.lock = threading.Lock()
        self.ready = threading.Event()
        exe = self.find_server()
        extra = ", backroomsLayoutVersion: %d" % layout if layout else ""
        cfg = "{ Port: %d, WorldConfig: { Seed: '12345', WorldType: 'backrooms', PlayStyle: 'backrooms'%s } }" % (port, extra)
        self.p = subprocess.Popen([exe, "--dataPath", data, "--addModPath", mods.replace("\\", "/"), "--withconfig", cfg],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
        threading.Thread(target=self.read, daemon=True).start()


def ask(srv, command, pattern, timeout=120):
    """Sends a command and returns the first server line after it that matches the pattern (or None)."""
    mark = srv.mark()
    srv.cmd(command)
    return srv.wait(lambda s: s if re.search(pattern, s) else None, mark, timeout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mods", required=True)
    ap.add_argument("--port", type=int, default=43280)
    ap.add_argument("--layout", type=int, default=0, help="layout version of the new world (passed as backroomsLayoutVersion; 0 = the build's CurrentVersion): 15 for a world without borax ore, 16 for one with")
    ap.add_argument("--washers", type=int, default=600)
    ap.add_argument("--skip-ore", action="store_true")
    ap.add_argument("--only-ore", action="store_true")
    ap.add_argument("--only-faceling", action="store_true")
    a = ap.parse_args()
    data = tempfile.mkdtemp(prefix="smalltest-")
    srv = LayoutServer(a.mods, data, a.port, a.layout)
    try:
        if not srv.ready.wait(600):
            print("FAIL: the server did not start")
            return 1
        time.sleep(3)
        n = a.washers
        for block in () if a.only_ore or a.only_faceling else ("icebox-north", "laundry-washer-north", "laundry-dryer-north", "supplybox-torn", "crate-open"):
            line = ask(srv, "/backrooms classdrops %s 0 0 %d" % (block, n), r"average per roll|No such block", 60)
            print((line or "no answer for " + block).split("] ", 1)[-1])
        fails = []
        if not a.skip_ore and not a.only_faceling:
            ore = None
            for _ in range(40):
                line = ask(srv, "/backrooms smalltest ore 8 4 48", r"smalltest ore: (Level|\d+ of)|Found nowhere|no such", 240)
                print((line or "no answer").split("] ", 1)[-1])
                if line and "Level 8" in line:
                    ore = line
                    break
                time.sleep(8)
            # Borax ore in Level 8 comes with layout 16 and not before
            m = re.search(r"layout version (\d+).*?borax (\d+)", ore or "")
            v = re.search(r"layout version (\d+)", ore or "")
            if not v:
                fails.append("ore: no Level 8 answer to check")
            else:
                borax = int(m.group(2)) if m else 0
                if int(v.group(1)) >= 16 and borax == 0:
                    fails.append("ore: no borax in Level 8 of a layout %s world" % v.group(1))
                elif int(v.group(1)) < 16 and borax > 0:
                    fails.append("ore: %d borax in Level 8 of a layout %s world" % (borax, v.group(1)))
        if a.only_ore:
            for f in fails:
                print("FAIL:", f)
            return 1 if fails else 0
        # A dummy to drink with (the first try may only load chunks)
        for _ in range(20):
            line = ask(srv, "/backrooms dummy place 0", r"Dummy #|Found nowhere|loading|try again", 60)
            if line and "Dummy #" in line:
                break
            time.sleep(4)
        for liquid in () if a.only_faceling else ("waterportion", "juiceportion-apple", "milkportion", "ciderportion-apple", "ciderportion-mead", "spiritportion-mead",
                       "vinegarportion", "honeyportion", "boilingwaterportion", "saltwaterportion"):
            for container in ("bowl-blue-fired", "jug-blue-fired"):
                line = ask(srv, "/backrooms smalltest sip %s 20 -1 %s" % (liquid, container), r"smalltest sip:|No such|Put a straw", 30)
                print((line or "no answer for " + liquid).split("] ", 1)[-1])
        # The Faceling's warning: a grown one set off by a noise at a dummy 3 blocks off stares first, then shoves
        line = None
        for _ in range(10):
            line = ask(srv, "/backrooms dummy place 0", r"Dummy #\d+ at|Found nowhere|loading|try again", 60)
            if line and re.search(r"Dummy #\d+ at", line):
                break
            time.sleep(4)
        print("dummy:", (line or "none").split("] ", 1)[-1])
        m = re.search(r"at (-?\d+) (-?\d+) (-?\d+)", line or "")
        if m:
            x, z = m.group(1), m.group(3)
            ask(srv, "/backrooms entitylog on", r"ntity|log", 10)
            mark = srv.mark()
            srv.cmd("/backrooms encounter faceling ambient %s %s 3" % (x, z))
            time.sleep(4)
            for l in srv.since(mark):
                print("  >", l[-200:])
            srv.cmd("/backrooms dummy noise 1")
            time.sleep(9)
            outburst = [l for l in srv.since(mark) if "outburst" in l]
            for l in outburst:
                print("FACELING:", l)
            tell = any("stares" in l for l in outburst) and any("shoves" in l for l in outburst)
            print("faceling tell: " + ("PASS" if tell else "FAIL (no stare and shove lines)"))
            if not tell:
                fails.append("faceling tell: no stare and shove lines")
        else:
            fails.append("faceling tell: no dummy placed")
        bad = [l for l in srv.since(0) if re.search(r"\[backrooms\].*(error|exception)|\[Server Error\]|vanilla drinks:", l, re.I)]
        for l in bad[:10]:
            print("LOG:", l)
        for f in fails:
            print("FAIL:", f)
        return 1 if bad or fails else 0
    finally:
        srv.stop()


if __name__ == "__main__":
    sys.exit(main())
