"""Headless tests for the early armour ladder (feedback round 2026-11, branch exp/fb-armour).

    python tools/aitest/armourtest.py --mods <Mods dir with backroomsss> [--port 43260] [--work DIR] [--only tables,conversion,recipes]

- tables: no startup errors; /backrooms armourtest for carpet vs gambeson (sewn-linen) vs leather vs none; /backrooms clanktest
  (how far a Hound hears a runner, jumper and walker in no armour, chain, lamellar and plate).
- recipes: /backrooms rig craft needs a player, so this only checks the log has no recipe errors and the item types loaded.
- conversion: a world made WITHOUT config/remaps.json holds pleather and pleather armour in a chest (/backrooms rig stash put);
  the same world is then loaded WITH it, and the chest must hold carpet squares and the same pieces of carpet armour, nothing lost.
"""
import argparse
import os
import re
import shutil
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run  # noqa: E402  (Server)

FAILS = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (" - " + detail if detail else ""), flush=True)
    if not ok:
        FAILS.append(name)


def boot(mods, data, port):
    srv = run.Server(mods, data, port)
    if not srv.ready.wait(1500):
        srv.stop()
        raise SystemExit("server did not start")
    time.sleep(5)
    return srv


def say(srv, cmd, secs=8):
    mark = srv.mark()
    srv.cmd(cmd)
    time.sleep(secs)
    return [l for l in srv.since(mark)]


def errors(srv):
    return [l for l in srv.since(0) if re.search(r"\[(Server )?Error\]|\[Warning\].*(recipe|Recipe|remap|Remap)", l)
            and "Missing" not in l[:0]]


def tables(mods, work, port):
    srv = boot(mods, os.path.join(work, "tables"), port)
    try:
        errs = errors(srv)
        check("no startup errors or recipe warnings", not errs, "; ".join(errs[:4]))
        for entity, level in (("hound", "3"), ("hound", "9"), ("skinstealer", "5")):
            out = say(srv, "/backrooms armourtest %s %s" % (entity, level), 4)
            for l in out:
                if "armourtest" in l and "blows to kill" in l:
                    print("   " + re.sub(r"^.*?armourtest", "armourtest", l))
        out = say(srv, "/backrooms armourtest hound 3 carpet", 4)
        check("armourtest knows the carpet set", any(" carpet:" in l and "no head piece" not in l for l in out), "\n".join(out[-3:]))
        out = say(srv, "/backrooms clanktest hound", 4)
        text = "\n".join(out)
        print("   " + text.replace("\n", "\n   "))
        check("clanktest: plate is heard from farther than chain than none", re.search(r"none\s+x1\.0.*?runner heard from ([\d.]+)", text, re.S) is not None
              and float(re.search(r"plate\s+x2\.0.*?runner heard from ([\d.]+)", text).group(1)) > float(re.search(r"chain\s+x1\.4.*?runner heard from ([\d.]+)", text).group(1))
              > float(re.search(r"none\s+x1\.0.*?runner heard from ([\d.]+)", text).group(1)))
        out = say(srv, "/backrooms blocksweep", 25)
        check("blocksweep", any("0 problems" in l or "no problems" in l.lower() for l in out), "\n".join(out[-3:]))
    finally:
        srv.stop()


def conversion(mods, work, port):
    data = os.path.join(work, "conversion")
    old = os.path.join(work, "mods-old")
    shutil.rmtree(old, ignore_errors=True)
    shutil.copytree(mods, old)
    removed = 0
    for root, _dirs, files in os.walk(old):
        for f in files:
            if f == "remaps.json":
                os.remove(os.path.join(root, f))
                removed += 1
    check("the no-remap copy of the mod has no remaps.json", removed == 1, "removed %d" % removed)
    srv = boot(old, data, port)
    try:
        out = say(srv, "/backrooms rig stash put", 4)
        check("phase 1: stash put", any("rig-stash put" in l for l in out), "\n".join(out[-2:]))
        out = say(srv, "/backrooms rig stash read", 4)
        before = [l for l in out if "rig-stash read" in l]
        print("   before: " + (before[-1] if before else "?"))
        check("phase 1: the chest holds pleather", bool(before) and "backrooms:pleather x7" in before[-1])
    finally:
        srv.stop()
    srv = boot(mods, data, port + 1)
    try:
        log = "\n".join(srv.since(0))
        print("   " + "\n   ".join(l for l in log.split("\n") if "emap" in l)[:600])
        out = say(srv, "/backrooms rig stash read", 4)
        after = [l for l in out if "rig-stash read" in l]
        print("   after:  " + (after[-1] if after else "?"))
        a = after[-1] if after else ""
        check("phase 2: pleather is carpet squares, 7 and 3 more (two stacks)", "backrooms:carpetsquare x7" in a and "backrooms:carpetsquare x3" in a and "pleather x" not in a.replace("armor-pleather", ""))
        check("phase 2: each pleather piece is the same piece of carpet armour", all(p in a for p in ("armor-carpet-body x1 dur 100", "armor-carpet-head x1", "armor-carpet-legs x1 dur 40")))
        check("phase 2: other things in the chest are untouched", "game:armor-body-sewn-leather x1 dur 500" in a)
        check("phase 2: no pleather left", "armor-pleather" not in a and "backrooms:pleather" not in a)
    finally:
        srv.stop()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mods", required=True)
    ap.add_argument("--port", type=int, default=43260)
    ap.add_argument("--work", default=os.path.join(tempfile.gettempdir(), "fbarmour-test"))
    ap.add_argument("--only", default="tables,conversion")
    args = ap.parse_args()
    os.makedirs(args.work, exist_ok=True)
    only = args.only.split(",")
    if "tables" in only:
        shutil.rmtree(os.path.join(args.work, "tables"), ignore_errors=True)
        tables(args.mods, args.work, args.port)
    if "conversion" in only:
        shutil.rmtree(os.path.join(args.work, "conversion"), ignore_errors=True)
        conversion(args.mods, args.work, args.port + 2)
    print("FAILED: " + ", ".join(FAILS) if FAILS else "ALL PASS")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
