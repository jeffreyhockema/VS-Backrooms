"""Renders docs/moddb-description.html the way the mod database shows it, for checking the page before pasting it.

    python tools/moddb_preview.py [out-dir] [--mobile]

Downloads the live page once (cached in out-dir), drops our description body into it in place of the live one, points the
image links at the local docs/moddb/img files, and screenshots it with headless Chrome into out-dir/preview.png and
tiles (preview-0.png, ...). Needs Chrome, Pillow and numpy.
"""
import os, re, subprocess, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = next((a for a in sys.argv[1:] if not a.startswith("--")), os.path.join(ROOT, "review", "moddb"))
MOBILE = "--mobile" in sys.argv
os.makedirs(OUT, exist_ok=True)
CHROME = next(p for p in ["C:/Program Files/Google/Chrome/Application/chrome.exe",
                          "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
                          "C:/Program Files/Microsoft/Edge/Application/msedge.exe"] if os.path.exists(p))

live = os.path.join(OUT, "live.html")
if not os.path.exists(live):
    req = urllib.request.Request("https://mods.vintagestory.at/backrooms", headers={"User-Agent": "Mozilla/5.0"})
    open(live, "wb").write(urllib.request.urlopen(req).read())
page = open(live, encoding="utf-8").read()
body = open(os.path.join(ROOT, "docs", "moddb-description.html"), encoding="utf-8").read()
body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
body = body.replace("https://raw.githubusercontent.com/jeffreyhockema/VS-Backrooms/main/docs/", "file:///" + ROOT.replace("\\", "/") + "/docs/")

# The live description runs from its <h1> (or our wrapper) to the files tab; keep the container's closing divs
a = page.index('<div class="tab-content description">')
a = page.index('<div style="clear:both;"><br></div>', a) + len('<div style="clear:both;"><br></div>')
b = page.index('<div class="tab-content files', a)
closers = re.search(r"((?:\s*</div>)+\s*)$", page[a:b]).group(1)
page = page[:a] + "\n" + body + closers + page[b:]
page = page.replace("<head>", '<head><base href="https://mods.vintagestory.at/">', 1)
html = os.path.join(OUT, "preview.html")
open(html, "w", encoding="utf-8").write(page)

width = 420 if MOBILE else 1400
shot = os.path.join(OUT, "preview.png")
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                f"--window-size={width},16000", "--virtual-time-budget=20000", f"--screenshot={shot}",
                "file:///" + html.replace("\\", "/")], capture_output=True)
from PIL import Image
import numpy as np
im = Image.open(shot)
rows = np.where(np.array(im.convert("L")).std(axis=1) > 2)[0]
h = int(rows.max()) + 1
for i, y in enumerate(range(0, h, 2400)):
    y2 = min(y + 2400, h)
    im.crop((0, y, width, y2)).save(os.path.join(OUT, f"preview-{i}.png"))
print(f"{h} px tall, {i + 1} tiles in {OUT}")
