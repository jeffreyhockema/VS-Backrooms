"""Render overview.bin (mapgen <seed> <R> overview) as a level map with a legend."""
import struct, sys
from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1], sys.argv[2]
d = open(src, "rb").read()
size = struct.unpack_from("<i", d, 0)[0]
cells = d[4:]

COL = {
    0: ((214, 190, 92), "Level 0, the Lobby"),
    1: ((150, 150, 146), "Level 1, the Habitable Zone"),
    2: ((60, 62, 68), "Level 2, Pipe Dreams"),
    3: ((150, 96, 60), "Level 3, the Electrical Station"),
    4: ((196, 200, 206), "Level 4, the Abandoned Office"),
    5: ((150, 40, 44), "Level 5, the Terror Hotel"),
    6: ((24, 24, 28), "Level 6, Lights Out"),
    11: ((255, 120, 200), "Level 6.1, the Snackrooms"),
    7: ((40, 86, 140), "Level 7, Thalassophobia"),
    8: ((112, 100, 84), "Level 8, Cave Systems"),
    9: ((70, 60, 110), "Level 9, the Suburbs"),
    10: ((170, 168, 84), "Level 10, Bumper Crop"),
}
OTHER = (230, 230, 230)

img = Image.new("RGB", (size, size))
px = img.load()
for j in range(size):
    for i in range(size):
        lv = cells[j * size + i]
        px[i, j] = COL[lv][0] if lv in COL else OTHER

scale = 1
c = size // 2
pad, sw, row = 24, 18, 26
legend_w = 300
W = size * scale + legend_w + pad
H = max(size * scale, pad * 2 + row * (len(COL) + 3))
canvas = Image.new("RGB", (W, H), (18, 18, 20))
canvas.paste(img, (0, 0))
dr = ImageDraw.Draw(canvas)
try:
    font = ImageFont.truetype("arial.ttf", 15)
    small = ImageFont.truetype("arial.ttf", 13)
except OSError:
    font = small = ImageFont.load_default()
# spawn marker
dr.ellipse((c - 4, c - 4, c + 4, c + 4), outline=(255, 255, 255), width=2)
x0 = size * scale + pad
y = pad
for lv in (0, 1, 2, 3, 4, 5, 6, 11, 7, 8, 9, 10):
    colour, name = COL[lv]
    dr.rectangle((x0, y, x0 + sw, y + sw), fill=colour, outline=(90, 90, 90))
    dr.text((x0 + sw + 10, y + 1), name, fill=(230, 230, 230), font=font)
    y += row
y += 10
dr.ellipse((x0 + 5, y + 4, x0 + 13, y + 12), outline=(255, 255, 255), width=2)
dr.text((x0 + sw + 10, y), "Where you wake", fill=(230, 230, 230), font=font)
y += row + 8
km = size * 32 / 1000
dr.text((x0, y), f"About {km:.0f} x {km:.0f} km around spawn,", fill=(170, 170, 170), font=small)
dr.text((x0, y + 18), "one pixel per 32-block cell.", fill=(170, 170, 170), font=small)
canvas.save(out, optimize=True)
print(out, canvas.size)
