"""Review screenshots of one experimental level, one client run at a time on this machine.

    python tools/clientrig/shots.py <level> --mods <Mods dir with backroomsss> --port <port> [--arrivals 3] [--torch] [--out DIR]

Takes the machine-wide rig lock (%TEMP%/backrooms-build/rig.lock: one game window at a time), then runs the client rig:
creative mode, the HUD off, optionally a lit torch in hand (dark levels), the level's showcase spots
(/backrooms showcase <level>, see src/Cheats/Showcase.cs) and a few random arrivals (/backrooms goto). Shots go to
<out>/<level>-NN-<name>.png and <level>-rN<a|b>.png, with a contact sheet <out>/sheet.jpg. Prints the out folder.
Look at the sheet and the single shots with an image viewer (the Read tool shows PNG/JPG).
"""
import argparse
import os
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
LOCK = os.path.join(os.environ.get("TEMP", "/tmp"), "backrooms-build", "rig.lock")


def take_lock():
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    waited = 0
    while True:
        try:
            os.mkdir(LOCK)
            return
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(LOCK) > 25 * 60:  # a dead run's lock
                    os.rmdir(LOCK)
                    continue
            except OSError:
                pass
            time.sleep(5)
            waited += 5
            if waited % 60 == 0:
                print(f"[shots] waiting for the rig lock ({waited}s)...", flush=True)


def keep_lock(stop):
    """Touches the lock now and then, so that a long run is never taken for a dead one's."""
    while not stop.wait(60):
        try:
            os.utime(LOCK, None)
        except OSError:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("level")
    ap.add_argument("--mods", required=True)
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--arrivals", type=int, default=3)
    ap.add_argument("--torch", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out = a.out or os.path.join(os.environ.get("TEMP", "/tmp"), "backrooms-shots", f"{a.level}-{stamp}")
    os.makedirs(out, exist_ok=True)
    steps = ['  - expect_no_startup_issues: ""', "  - bot: closeguis", "  - bot: cmd /gamemode creative",
             "  - bot: wait 1500", "  - bot: hud off"]
    if a.torch:
        steps += ["  - bot: cmd /giveblock torch-basic-lit-up 1", "  - bot: wait 1000", "  - bot: slot 1"]  # (slot 0 holds the starting note)
    steps.append(f"  - showcase: {a.level}")
    for r in range(a.arrivals):
        h = (r * 113) % 360
        steps += [f"  - bot: cmd /backrooms goto {a.level}", "  - bot: movewait", "  - bot: ready 48", "  - bot: wait 3000",
                  "  - bot: closeguis", f"  - bot: look {h} 0", f"  - shot: {a.level}-r{r}a", f"  - bot: look {(h + 180) % 360} -8",
                  f"  - shot: {a.level}-r{r}b"]
    steps.append("  - expect_no_log: Unhandled exception")
    scen = os.path.join(out, "scenario.yaml")
    with open(scen, "w", encoding="utf-8") as f:
        f.write(f"description: Review shots of Level {a.level}\nsteps:\n" + "\n".join(steps) + "\n")
    take_lock()
    r = None
    stop = threading.Event()
    threading.Thread(target=keep_lock, args=(stop,), daemon=True).start()
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, "rig.py"), "--mods", a.mods, "--scenario", scen,
                            "--port", str(a.port), "--out", out], cwd=REPO)
    finally:
        stop.set()
        try:
            os.rmdir(LOCK)
        except OSError:
            pass
    shots_dir = os.path.join(out, "scenario")
    pngs = sorted(f for f in os.listdir(shots_dir) if f.endswith(".png")) if os.path.isdir(shots_dir) else []
    try:
        from PIL import Image, ImageDraw
        W, H, cols = 640, 360, 3
        rows = (len(pngs) + cols - 1) // cols
        if rows:
            sheet = Image.new("RGB", (W * cols, H * rows), (20, 20, 20))
            d = ImageDraw.Draw(sheet)
            for k, f in enumerate(pngs):
                im = Image.open(os.path.join(shots_dir, f)).convert("RGB").resize((W, H))
                sheet.paste(im, ((k % cols) * W, (k // cols) * H))
                d.text(((k % cols) * W + 6, (k // cols) * H + 4), f, fill=(255, 255, 0))
            sheet.save(os.path.join(out, "sheet.jpg"), quality=80)
    except Exception as e:  # noqa: BLE001
        print("[shots] no contact sheet:", e)
    print(f"[shots] {len(pngs)} shots in {shots_dir}; sheet {os.path.join(out, 'sheet.jpg')}; rig exit {r.returncode if r else 'none'}")


if __name__ == "__main__":
    main()
