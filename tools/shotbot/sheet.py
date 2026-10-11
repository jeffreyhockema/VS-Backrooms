import sys, os, glob
from PIL import Image, ImageDraw
names = sys.argv[2:]; out = sys.argv[1]
W, H, COLS = 640, 360, 3
rows = (len(names) + COLS - 1) // COLS
sheet = Image.new("RGB", (W * COLS, (H + 18) * rows), (20, 20, 20))
d = ImageDraw.Draw(sheet)
for i, n in enumerate(names):
    p = f"shots/{n}.png"
    if not os.path.exists(p): continue
    im = Image.open(p).resize((W, H))
    x, y = (i % COLS) * W, (i // COLS) * (H + 18)
    sheet.paste(im, (x, y + 18)); d.text((x + 4, y + 3), n, fill=(255, 255, 255))
sheet.save(out)
