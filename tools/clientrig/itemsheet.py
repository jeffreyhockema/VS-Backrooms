"""Item contact sheets from the real client: one rig run for all the items, then a sheet per item and an index.

    python tools/clientrig/itemsheet.py --mods <Mods dir with backroomsss> --port 43410 --out <dir> <code> [<code> ...]
    python tools/clientrig/itemsheet.py --mods <Mods> --port 43410 --out <dir> --list codes.txt     (one code per line, # comments)
    python tools/clientrig/itemsheet.py ... --dry-run      (writes the scenario and validates it; launches nothing)

A code is a Backrooms item code (almondwater, wanderernote-cache) or domain:code (game:flint).
Level 10 by day (an open field, nothing behind the camera), creative so nothing hurts. Per item: /backrooms rig itemshow puts it in the
selected hotbar slot and on the floor 2 blocks ahead; then four shots: its handbook page (the inventory icon, large), first person
holding it (HUD on: the game hides the hand with the GUIs), third person (zoomed), and a close look at it on the ground. Output in <out>: <code>.jpg (the four, labelled),
index.jpg (all items), and the rig's own report (itemsheet/report.md, shots, logs). The scenario is <out>/itemsheet.json.
The client is single-instance: rig.py waits for a free one.
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "shotbot"))
import batch  # noqa: E402

VIEWS = [("icon", "inventory icon (handbook)"), ("fp", "first person"), ("tp", "third person"), ("ground", "on the ground")]


def slug(code):
    return re.sub(r"[^a-z0-9-]", "_", code.lower())


def handbook_page(code):
    """Handbook page id of an item code: item-<code>, with the domain kept unless it is the game's."""
    if code.startswith("game:"):
        return "item-" + code[5:]
    return "item-" + (code if ":" in code else "backrooms:" + code)


def scenario(codes):
    st = [
        {"expect_no_startup_issues": ""},
        {"bot": "closeguis"}, {"bot": "hud off"}, {"bot": "wait 3000"}, {"bot": "ready 48"},
        {"cmd": "/backrooms heal"}, {"cmd": "/backrooms director off"}, {"cmd": "/gamemode creative"},
        {"server": "/time setmonth jun"}, {"server": "/time set 12:00"},
        {"cmd": "/backrooms goto 10 timeout=60"}, {"bot": "movewait"}, {"bot": "ready 48"},
        {"bot": "daylight"}, {"bot": "slot 0"}, {"bot": "look 0 0"}, {"bot": "wait 1500"},
    ]
    for code in codes:
        s = slug(code)
        st += [
            {"cmd": "/backrooms rig itemshow " + code},
            {"expect_chat": "rig-itemshow"},
            {"bot": "wait 1200"},
            # the handbook page: the icon, large
            {"bot": "hud on"}, {"bot": "handbook " + handbook_page(code)}, {"bot": "wait 1500"}, {"shot": s + "-icon"},
            {"bot": "closeguis"}, {"bot": "hud off"},
            # first person, looking a little down so the hand and the item on the floor are both in view; the HUD on, because the game
            # does not draw the first-person hand while the GUIs are hidden (EntityPlayerShapeRenderer: FirstPerson && HideGuis returns)
            {"bot": "hud on"}, {"bot": "fov 70"}, {"bot": "look 0 -12"}, {"bot": "wait 900"}, {"shot": s + "-fp"}, {"bot": "hud off"},
            # third person, a little zoomed: head to knees, so the hands and what is in them are in the frame (fov 28 cut them off)
            {"bot": "hotkey cyclecamera"}, {"bot": "fov 48"}, {"bot": "look 0 -15"}, {"bot": "wait 1200"}, {"shot": s + "-tp"},
            {"bot": "hotkey cyclecamera"}, {"bot": "hotkey cyclecamera"}, {"bot": "fov 70"}, {"bot": "wait 600"},
            # on the ground, close: a narrow view down at the item 2 blocks ahead
            {"bot": "fov 30"}, {"bot": "look 0 -40"}, {"bot": "wait 900"}, {"shot": s + "-ground"},
            {"bot": "fov 70"}, {"bot": "look 0 0"},
        ]
    st += [{"expect_no_log": "Did not find"}, {"expect_no_log": "Exception:"}]
    return {"description": "Item contact sheets (tools/clientrig/itemsheet.py): " + ", ".join(codes), "steps": st}


def sheet(folder, code, out):
    from PIL import Image, ImageDraw
    s = slug(code)
    w, h = 640, 360
    img = Image.new("RGB", (w * 2, (h + 20) * 2 + 24), (20, 20, 20))
    d = ImageDraw.Draw(img)
    d.text((6, 6), code, fill=(255, 255, 160))
    for i, (key, label) in enumerate(VIEWS):
        x, y = (i % 2) * w, 24 + (i // 2) * (h + 20)
        p = next((os.path.join(folder, s + "-" + key + e) for e in (".png", ".jpg") if os.path.exists(os.path.join(folder, s + "-" + key + e))), None)
        d.text((x + 4, y + 4), label, fill=(255, 255, 255))
        if p:
            shot = Image.open(p).convert("RGB")
            if key == "icon":  # the handbook dialog is small in a big frame: the icon and the name beside it, enlarged
                W, H = shot.size
                shot = shot.crop((int(.35 * W), int(.09 * H), int(.50 * W), int(.22 * H)))
            img.paste(shot.resize((w, h), Image.LANCZOS), (x, y + 20))
        else:
            d.rectangle((x, y + 20, x + w - 1, y + 20 + h - 1), outline=(255, 0, 255))
            d.text((x + 8, y + 30), "MISSING", fill=(255, 0, 255))
    img.save(out, quality=88)


def index(out, codes):
    from PIL import Image, ImageDraw
    cols, w = 3, 640
    tiles = []
    for c in codes:
        p = os.path.join(out, slug(c) + ".jpg")
        if os.path.exists(p):
            tiles.append(Image.open(p).convert("RGB"))
    if not tiles:
        return
    h = int(tiles[0].height * w / tiles[0].width)
    rows = (len(tiles) + cols - 1) // cols
    img = Image.new("RGB", (cols * w, rows * h), (20, 20, 20))
    for i, t in enumerate(tiles):
        img.paste(t.resize((w, h), Image.LANCZOS), ((i % cols) * w, (i // cols) * h))
    img.save(os.path.join(out, "index.jpg"), quality=85)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mods", required=True)
    ap.add_argument("--port", type=int, default=42797)
    ap.add_argument("--out", required=True)
    ap.add_argument("--list", help="a file of item codes, one per line")
    ap.add_argument("--seed", default="424242")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("codes", nargs="*")
    a = ap.parse_args()
    codes = list(a.codes)
    if a.list:
        codes += [l.split("#")[0].strip() for l in open(a.list, encoding="utf-8") if l.split("#")[0].strip()]
    if not codes:
        sys.exit("no item codes given")
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    scen = os.path.join(out, "itemsheet.json")
    with open(scen, "w", encoding="utf-8") as f:
        json.dump(scenario(codes), f, indent=1)
    cmd = [sys.executable, os.path.join(HERE, "rig.py"), "--mods", a.mods, "--scenario", scen, "--port", str(a.port), "--seed", a.seed, "--out", out]
    if a.dry_run:
        cmd.append("--dry-run")
    r = subprocess.run(cmd)
    if a.dry_run:
        sys.exit(r.returncode)
    folder = os.path.join(out, "itemsheet")
    for c in codes:
        sheet(folder, c, os.path.join(out, slug(c) + ".jpg"))
    index(out, codes)
    print("sheets in", out)
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
