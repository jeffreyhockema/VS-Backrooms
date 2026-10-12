"""Builds the ModDB cover (480x480, required size) and a wide 1920x1080 banner from an in-game screenshot."""
import os, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
SRC = os.path.join(REPO, "docs", "screenshots", "01-level0-where-you-wake.png")
OUT = os.path.join(REPO, "docs", "cover")
os.makedirs(OUT, exist_ok=True)
FONT = r"C:\Windows\Fonts\bahnschrift.ttf"

TITLE_COL = (246, 238, 205)      # fluorescent off-white
SUB_COL = (238, 226, 172)        # wallpaper yellow, lighter


def font(size, style):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_name(style)
    except Exception:
        pass
    return f


def tracked(draw, xy, text, f, fill, tracking, anchor_center=True):
    """Draws text with extra letter spacing; xy is the centre of the baseline row if anchor_center."""
    widths = [draw.textlength(ch, font=f) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x, y = xy
    if anchor_center:
        x -= total / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=f, fill=fill)
        x += w + tracking
    return total


def grade(im):
    """A little darker and warmer at the edges, as under failing lights; light grain."""
    im = ImageEnhance.Contrast(im).enhance(1.06)
    w, h = im.size
    # vignette
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((-w * 0.25, -h * 0.2, w * 1.25, h * 1.25), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(w * 0.12))
    dark = Image.new("RGB", (w, h), (18, 15, 6))
    im = Image.composite(im, dark, mask.point(lambda v: int(70 + v * 185 / 255)))
    return im


def top_shade(im, frac, strength):
    w, h = im.size
    shade = Image.new("L", (w, h), 0)
    sd = ImageDraw.Draw(shade)
    stop = int(h * frac)
    for y in range(stop):
        sd.line([(0, y), (w, y)], fill=int(strength * (1 - y / stop) ** 1.6))
    return Image.composite(Image.new("RGB", (w, h), (10, 9, 4)), im, shade)


def bottom_shade(im, frac, strength):
    w, h = im.size
    shade = Image.new("L", (w, h), 0)
    sd = ImageDraw.Draw(shade)
    start = int(h * (1 - frac))
    for y in range(start, h):
        sd.line([(0, y), (w, y)], fill=int(strength * ((y - start) / (h - start)) ** 1.8))
    return Image.composite(Image.new("RGB", (w, h), (10, 9, 4)), im, shade)


def title_block(canvas, cx, top, width):
    """BACKROOMS fitted to width, SURVIVAL STORY under it with a rule either side."""
    d = ImageDraw.Draw(canvas)
    # fit the title
    size = 400
    while True:
        f = font(size, "Bold Condensed")
        tracking = size * 0.04
        tw = sum(d.textlength(c, font=f) for c in "BACKROOMS") + tracking * 8
        if tw <= width or size < 20:
            break
        size -= 2
    asc, desc = f.getmetrics()
    # soft shadow layer
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    tracked(sdraw, (cx, top + size * 0.03), "BACKROOMS", f, (0, 0, 0, 200), tracking)
    sub_size = int(size * 0.31)
    fs = font(sub_size, "SemiBold")
    sub_track = sub_size * 0.26
    sub_y = top + asc * 0.98
    tracked(sdraw, (cx, sub_y + sub_size * 0.04), "SURVIVAL STORY", fs, (0, 0, 0, 200), sub_track)
    shadow = shadow.filter(ImageFilter.GaussianBlur(size * 0.04))
    canvas.paste(shadow, (0, 0), shadow)
    # glow: the title lit like a sign under the troffers
    glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    tracked(gdraw, (cx, top), "BACKROOMS", f, (255, 240, 170, 90), tracking)
    glow = glow.filter(ImageFilter.GaussianBlur(size * 0.06))
    canvas.paste(glow, (0, 0), glow)
    d = ImageDraw.Draw(canvas)
    tracked(d, (cx, top), "BACKROOMS", f, TITLE_COL, tracking)
    sw = tracked(d, (cx, sub_y), "SURVIVAL STORY", fs, SUB_COL, sub_track)
    # rules either side of the subtitle
    ry = sub_y + fs.getmetrics()[0] * 0.55
    gap = sub_size * 0.45
    half = width / 2
    lw = max(2, int(sub_size * 0.07))
    d.line([(cx - half, ry), (cx - sw / 2 - gap, ry)], fill=SUB_COL, width=lw)
    d.line([(cx + sw / 2 + gap, ry), (cx + half, ry)], fill=SUB_COL, width=lw)
    return sub_y + fs.getmetrics()[0]


def grain(im, amount, seed=7):
    random.seed(seed)
    noise = Image.effect_noise(im.size, 40).convert("L")
    noise = noise.point(lambda v: int((v - 128) * amount + 128))
    return Image.blend(im, Image.merge("RGB", (noise, noise, noise)), 0.06)


def cover():
    src = Image.open(SRC).convert("RGB")
    w, h = src.size
    # square: keep the box and the hall; a little left of centre to hold the pillars
    side = h
    left = (w - side) // 2 - 40
    sq = src.crop((left, 0, left + side, side)).resize((1440, 1440), Image.LANCZOS)
    sq = grade(sq)
    sq = top_shade(sq, 0.42, 215)
    sq = bottom_shade(sq, 0.18, 120)
    title_block(sq, 720, 70, 1290)
    sq = grain(sq, 1.0)
    sq.save(os.path.join(OUT, "cover-1440.png"))
    small = sq.resize((480, 480), Image.LANCZOS)
    small = small.filter(ImageFilter.UnsharpMask(radius=1.0, percent=60, threshold=2))
    small.save(os.path.join(OUT, "cover-480.png"), optimize=True)
    print("cover", small.size)


def banner():
    src = Image.open(SRC).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    im = grade(src)
    im = top_shade(im, 0.40, 210)
    im = bottom_shade(im, 0.16, 110)
    title_block(im, 960, 52, 1100)
    im = grain(im, 1.0)
    im.save(os.path.join(OUT, "banner-1920x1080.png"), optimize=True)
    print("banner", im.size)


if __name__ == "__main__":
    cover()
    banner()
