"""Level 36, "Airport" (experimental): textures of the airliner cabin (LIMINAL AIR): window views, signs and placards,
doors, fuselage skin, galley, soft furnishings, row numbers. All fully opaque (alpha 255). Deterministic.
Writes assets/backrooms/textures/block/36/cabin/*.png. Run: python tools/gen_36_cabin_tex.py
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from gen_3999_kit import F3, F5, draw_text, text_width
from gen_36_surfaces_signs import DIN, DIN_COND, DIN_SEMI, text_mask, pict_runner, pict_plane

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "assets", "backrooms", "textures", "block", "36", "cabin")

PLASTIC = (228, 226, 218)
NAVY = (34, 46, 98)
TEAL = (18, 92, 120)
AMBER = (255, 200, 80)
WHITE = (246, 250, 246)
CHAR = (40, 42, 47)
SKIN = (236, 238, 240)
RED = (214, 36, 34)


# ------------------------------------------------------------------ helpers

def arr(img):
    return np.asarray(img.convert("RGB"), dtype=np.float32).copy()


def img_of(a):
    return Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8), "RGB")


def flat(w, h, col, amp=2.0, seed=0):
    r = np.random.RandomState(seed)
    a = np.empty((h, w, 3), np.float32)
    a[:] = col
    a += r.uniform(-amp, amp, (h, w))[..., None]
    return img_of(a)


def vgrad(w, h, stops):
    ys = np.linspace(0, 1, h)
    out = np.zeros((h, w, 3), np.float32)
    for c in range(3):
        col = np.interp(ys, [s[0] for s in stops], [s[1][c] for s in stops])
        out[:, :, c] = col[:, None]
    return out


def vnoise(w, h, cw, ch, seed):
    gw, gh = max(2, int(round(w / cw)) + 1), max(2, int(round(h / ch)) + 1)
    g = np.random.RandomState(seed).rand(gh, gw).astype(np.float32)
    im = Image.fromarray(g, "F").resize((w, h), Image.BICUBIC)
    return np.asarray(im, dtype=np.float32)


def rect(img, x0, y0, x1, y1, col):
    """Pixel rectangle [x0,x1) x [y0,y1)."""
    ImageDraw.Draw(img).rectangle([x0, y0, x1 - 1, y1 - 1], fill=col)


def outline(img, x0, y0, x1, y1, col):
    ImageDraw.Draw(img).rectangle([x0, y0, x1 - 1, y1 - 1], outline=col)


def px(img, x, y, col):
    if 0 <= x < img.size[0] and 0 <= y < img.size[1]:
        img.putpixel((x, y), tuple(int(v) for v in col))


def scale(c, f):
    return tuple(int(max(0, min(255, v * f))) for v in c)


def mixc(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def bevel(img, box, lift=0.14, drop=0.18):
    """1 px light top/left, dark bottom/right (box = x0,y0,x1,y1 exclusive)."""
    a = arr(img)
    x0, y0, x1, y1 = box
    a[y0, x0:x1] *= 1 + lift
    a[y0:y1, x0] *= 1 + lift
    a[y1 - 1, x0:x1] *= 1 - drop
    a[y0:y1, x1 - 1] *= 1 - drop
    return img_of(a)


class Ov:
    """A supersampled RGBA overlay in native pixel coordinates, composited down with a box filter."""

    def __init__(s, w, h, k=4):
        s.w, s.h, s.k = w, h, k
        s.im = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0))
        s.d = ImageDraw.Draw(s.im)

    @staticmethod
    def c(col):
        return tuple(int(v) for v in col[:3]) + (255,)

    def P(s, pts):
        return [(x * s.k, y * s.k) for x, y in pts]

    def poly(s, pts, col, outline=None, width=0.0):
        s.d.polygon(s.P(pts), fill=s.c(col))
        if outline:
            q = s.P(list(pts) + [pts[0]])
            s.d.line(q, fill=s.c(outline), width=max(1, int(width * s.k)), joint="curve")

    def rect(s, x0, y0, x1, y1, col):
        s.d.rectangle([x0 * s.k, y0 * s.k, x1 * s.k - 1, y1 * s.k - 1], fill=s.c(col))

    def rrect(s, x0, y0, x1, y1, r, col, outline=None, width=0.0):
        s.d.rounded_rectangle([x0 * s.k, y0 * s.k, x1 * s.k - 1, y1 * s.k - 1], radius=r * s.k, fill=s.c(col),
                              outline=s.c(outline) if outline else None, width=int(width * s.k))

    def ell(s, cx, cy, rx, ry, col):
        s.d.ellipse([(cx - rx) * s.k, (cy - ry) * s.k, (cx + rx) * s.k - 1, (cy + ry) * s.k - 1], fill=s.c(col))

    def ring(s, cx, cy, r, wd, col):
        s.d.ellipse([(cx - r) * s.k, (cy - r) * s.k, (cx + r) * s.k - 1, (cy + r) * s.k - 1], outline=s.c(col),
                    width=max(1, int(wd * s.k)))

    def line(s, pts, col, wd):
        s.d.line(s.P(pts), fill=s.c(col), width=max(1, int(wd * s.k)), joint="curve")
        r = wd * s.k / 2
        for x, y in (pts[0], pts[-1]):
            s.d.ellipse([x * s.k - r, y * s.k - r, x * s.k + r, y * s.k + r], fill=s.c(col))

    def small(s):
        return s.im.resize((s.w, s.h), Image.BOX)

    def apply(s, img):
        sm = s.small()
        img.paste(sm, (0, 0), sm)
        return img

    def alpha(s):
        return s.small().getchannel("A")

    def apply_src(s, img, src):
        img.paste(src, (0, 0), s.alpha())
        return img


def text(img, s, box, col, spec=DIN, max_px=None, k=8, tracking=0):
    w, h = img.size
    m, p = text_mask((w * k, h * k), s, spec, tuple(int(v * k) for v in box), int((max_px or h) * k), "centre", 8,
                     tracking)
    m = m.resize((w, h), Image.BOX)
    img.paste(Image.new("RGB", (w, h), col), (0, 0), m)
    return p / k


def pix_text(img, s, cx, y, col, font=F3, gap=1):
    w = text_width(s, font, 1, gap)
    draw_text(img, s, int(cx - w / 2), y, col, font, 1, gap)


def shapes(img, fn, col, k=8):
    w, h = img.size
    m = Image.new("L", (w * k, h * k), 0)
    fn(ImageDraw.Draw(m), k)
    m = m.resize((w, h), Image.BOX)
    img.paste(Image.new("RGB", (w, h), col), (0, 0), m)


def save(img, name, size):
    img = img.convert("RGB")
    assert img.size == size, (name, img.size, size)
    os.makedirs(OUT, exist_ok=True)
    img.convert("RGBA").save(os.path.join(OUT, name + ".png"))


def blur_x(a, n):
    k = 1.0 / n
    p = n // 2
    pad = np.pad(a, ((0, 0), (p, p), (0, 0)), mode="edge")
    out = np.zeros_like(a)
    for i in range(n):
        out += pad[:, i:i + a.shape[1]] * k
    return out


def brushed(w, h, base, seed, amp=3.5, horizontal=True):
    r = np.random.RandomState(seed)
    if horizontal:
        a = np.empty((h, w, 3), np.float32)
        a[:] = base
        a += r.uniform(-amp, amp, (h, 1))[..., None] + r.uniform(-1.2, 1.2, (h, w))[..., None]
        a = blur_x(a, 3)
        a += np.linspace(-1, 1, w)[None, :, None] ** 2 * -4 + 3
    else:
        a = np.empty((h, w, 3), np.float32)
        a[:] = base
        a += r.uniform(-amp, amp, (1, w))[..., None] + r.uniform(-1.2, 1.2, (h, w))[..., None]
        a = blur_x(a.transpose(1, 0, 2), 3).transpose(1, 0, 2)
        a += np.linspace(-1, 1, h)[:, None, None] ** 2 * -3 + 2
    return img_of(a)


# ------------------------------------------------------------------ window views (32x48)

def view_apron():
    w, h = 32, 48
    a = np.zeros((h, w, 3), np.float32)
    a[:23] = vgrad(w, 23, [(0, (194, 200, 206)), (1, (226, 229, 231))])
    a[23:] = vgrad(w, 25, [(0, (158, 160, 160)), (1, (122, 124, 125))])
    img = img_of(a)
    d = ImageDraw.Draw(img)
    rnd = random.Random(36001)
    d.rectangle([0, 13, 7, 18], fill=(156, 162, 170))
    d.line([0, 13, 7, 13], fill=(184, 188, 194))
    d.rectangle([0, 17, 31, 18], fill=(178, 182, 188))
    d.rectangle([0, 19, 31, 22], fill=(108, 126, 146))
    d.line([0, 19, 31, 19], fill=(150, 160, 172))
    for x in range(1, 32, 3):
        d.line([x, 19, x, 22], fill=(194, 200, 206))
    for _ in range(7):
        px(img, rnd.randrange(32), rnd.randrange(20, 23), (232, 216, 166))
    for xb in (-34, -14, 5, 27, 46, 66):
        d.line([16, 23, xb, 47], fill=(142, 144, 144))
    for y in (26, 30, 36, 44):
        d.line([0, y, 31, y], fill=(140, 142, 142))
    img = img_of(arr(img) + np.random.RandomState(7).uniform(-1.5, 1.5, (h, w))[..., None])
    o = Ov(w, h, 8)
    L, R = [], []
    for i in range(0, 21):
        s_ = i / 20
        cx = 16 + 3.0 * s_ * s_ - 1.5 * s_
        wd = 0.25 + 1.9 * s_
        y = 23 + 25.5 * s_
        L.append((cx - wd, y))
        R.append((cx + wd, y))
    o.poly(L + R[::-1], (240, 196, 40))
    o.poly([(5.5, 40), (8.5, 40), (7.6, 36.4), (6.4, 36.4)], (232, 110, 30))
    o.rect(5, 40, 9, 41, (60, 60, 64))
    o.ell(25.5, 41.2, 7.5, 1.1, (104, 106, 107))
    o.rect(20, 35.5, 25.4, 39.2, (232, 144, 34))
    o.rect(20.6, 33.2, 23.4, 35.6, (222, 132, 30))
    o.rect(21, 33.7, 23, 35, (120, 160, 190))
    o.line([(25.2, 38.2), (26.2, 38.6)], (50, 50, 54), 0.4)
    o.rect(26, 38, 31.6, 39.2, (96, 100, 106))
    o.rect(26.4, 35.2, 28.8, 38, (72, 84, 112))
    o.rect(29, 36.2, 31.2, 38, (150, 72, 62))
    o.rect(26.4, 35.2, 28.8, 35.7, (96, 108, 138))
    for cx, cy in ((21.5, 40.1), (24.3, 40.1), (27.2, 40.1), (30.4, 40.1)):
        o.ell(cx, cy, 1.1, 1.1, (30, 30, 34))
    o.apply(img)
    return img


def view_roll():
    w, h = 32, 48
    r = np.random.RandomState(36002)
    a = np.zeros((h, w, 3), np.float32)
    a[:21] = vgrad(w, 21, [(0, (128, 148, 180)), (1, (192, 206, 224))])
    for y in range(21, h):
        t = (y - 21) / 26.0
        if y < 25:
            f = (y - 21) / 4.0
            base = np.array((100, 114, 96), np.float32) * (1 - f) + np.array((92, 126, 74), np.float32) * f
        elif y < 33:
            base = np.array((84, 130, 68), np.float32) * (0.9 + 0.2 * t)
        elif y < 37:
            base = np.array((90, 96, 90), np.float32)
        else:
            base = np.array((86, 88, 94), np.float32) * (1.05 - 0.4 * t)
        a[y, :, :] = base
    st = vnoise(w, h, 22, 1.0, 5)
    st2 = vnoise(w, h, 9, 1.0, 6)
    amp = np.clip((np.arange(h) - 20) / 27.0, 0, 1)[:, None] * 46 + 5
    a += (((st - 0.5) * 1.2 + (st2 - 0.5) * 0.8) * amp)[..., None]
    a = blur_x(a, 7)
    line = vnoise(w, h, 14, 8, 9)
    for y in range(33, 37):
        f = {33: 0.35, 34: 1.0, 35: 1.0, 36: 0.4}[y]
        a[y] = a[y] * (1 - f) + np.array((240, 242, 238), np.float32) * f * (0.85 + 0.3 * line[y][:, None])
    a[44:46] = a[44:46] * 0.75 + np.array((200, 200, 196), np.float32) * 0.25 * (0.4 + line[44:46, :, None])
    return img_of(a + r.uniform(-1.5, 1.5, (h, w))[..., None])


def view_climb():
    sw, sh = 192, 256
    rnd = random.Random(36003)
    hz = 108
    a = np.zeros((sh, sw, 3), np.float32)
    a[:hz] = vgrad(sw, hz, [(0, (66, 120, 196)), (0.7, (118, 168, 222)), (1, (186, 212, 236))])
    img = img_of(a)
    d = ImageDraw.Draw(img)
    fields = [(112, 152, 82), (142, 168, 86), (192, 182, 104), (98, 130, 74), (156, 136, 92), (170, 176, 98),
              (124, 156, 90), (208, 196, 120)]
    y = hz
    haze = (176, 204, 226)
    while y < sh + 20:
        rh = 3 + (y - hz) * 0.16
        x = -rnd.uniform(0, 30)
        while x < sw + 40:
            cw = rh * rnd.uniform(1.4, 4.2)
            c = scale(rnd.choice(fields), rnd.uniform(0.9, 1.08))
            c = mixc(c, haze, max(0.0, 1 - (y - hz) / 60.0) * 0.75)
            d.rectangle([x, y, x + cw, y + rh], fill=c, outline=scale(c, 0.86))
            x += cw
        y += rh
    tx, ty, tw, th = 52, 168, 62, 36
    d.rectangle([tx, ty, tx + tw, ty + th], fill=(150, 150, 156))
    for gx in range(tx + 4, tx + tw - 4, 7):
        for gy in range(ty + 4, ty + th - 4, 6):
            if rnd.random() < 0.8:
                d.rectangle([gx, gy, gx + 4, gy + 3], fill=rnd.choice([(118, 112, 112), (176, 150, 130), (126, 128, 136)]))
    d.line([tx, ty + 18, tx + tw, ty + 18], fill=(206, 206, 204), width=2)
    d.line([tx + 30, ty, tx + 30, ty + th], fill=(206, 206, 204), width=2)
    d.rectangle([tx + 70, ty + 14, tx + 100, ty + 24], fill=(96, 120, 150))
    img = img.rotate(15, resample=Image.BICUBIC)
    cx, cy = sw // 2, sh // 2 - 10
    img = img.crop((cx - 64, cy - 96, cx + 64, cy + 96)).resize((32, 48), Image.BOX)
    o = Ov(32, 48, 8)
    o.poly([(32, 35.2), (22, 37.6), (14, 40.6), (12.3, 42.6), (12.9, 44.6), (16, 45.4), (32, 48.4)], (240, 244, 246))
    o.poly([(32, 42.2), (20, 42.8), (13.2, 43.2), (13, 44.7), (16, 45.4), (32, 48.4)], (206, 214, 222))
    o.poly([(32, 35.2), (22, 37.6), (14, 40.6), (14, 40.9), (22, 38.6), (32, 36.4)], (255, 255, 255))
    o.poly([(12.6, 43), (9.6, 31.5), (11.8, 30.4), (15.6, 41.4)], (242, 246, 248), outline=(190, 200, 210), width=0.15)
    o.poly([(9.6, 31.5), (11.8, 30.4), (12.9, 34.6), (10.5, 35.2)], TEAL)
    o.apply(img)
    g = Ov(32, 48, 8)
    g.ell(12.7, 44.0, 2.6, 2.6, (110, 230, 150))
    img.paste(Image.new("RGB", (32, 48), (120, 255, 160)), (0, 0), g.alpha().point(lambda v: int(v * 0.35)))
    o = Ov(32, 48, 8)
    o.ell(12.7, 44.0, 1.0, 1.0, (60, 255, 120))
    o.ell(12.5, 43.8, 0.5, 0.5, (190, 255, 205))
    o.apply(img)
    return img


def _smooth(t):
    return t * t * (3 - 2 * t)


def tnoise(G, u, v):
    n = G.shape[0]
    u0, v0 = np.floor(u).astype(int), np.floor(v).astype(int)
    fu, fv = _smooth(u - u0), _smooth(v - v0)

    def g(i, j):
        return G[j % n, i % n]
    return (g(u0, v0) * (1 - fu) + g(u0 + 1, v0) * fu) * (1 - fv) + (g(u0, v0 + 1) * (1 - fu) + g(u0 + 1, v0 + 1) * fu) * fv


def view_cruise():
    w, h = 32, 48
    hz = 25
    a = np.zeros((h, w, 3), np.float32)
    a[:hz + 1] = vgrad(w, hz + 1, [(0, (6, 18, 64)), (0.5, (24, 64, 140)), (0.85, (84, 150, 212)), (1, (178, 206, 232))])
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    sunx = 4.0
    dist = np.sqrt((xx - sunx) ** 2 + ((yy - (hz + 0.5)) * 1.3) ** 2)
    glow = np.exp(-(dist / 9.0) ** 2)
    warm = np.array((255, 168, 84), np.float32)
    sky = yy <= hz
    a[sky] = a[sky] * (1 - 0.8 * glow[sky][:, None]) + warm * 0.8 * glow[sky][:, None]
    G = np.random.RandomState(36004).rand(32, 32).astype(np.float32)
    G2 = np.random.RandomState(36005).rand(32, 32).astype(np.float32)
    xs = np.arange(w)
    for y in range(hz + 1, h):
        dy = y - hz + 0.3
        z = 5.0 / dy
        u = (xs - 16) * z * 0.55 + 16
        v = np.full(w, z * 1.8 + 2.0)
        n = 0.65 * tnoise(G, u * 0.5, v * 0.5) + 0.35 * tnoise(G2, u * 1.3, v * 1.3)
        n = np.clip((n - 0.3) * 2.0, 0, 1)
        shadow = np.array((140, 160, 202), np.float32)
        cream = np.array((252, 246, 232), np.float32)
        col = shadow[None] * (1 - n[:, None]) + cream[None] * n[:, None]
        g = np.exp(-(((xs - sunx) ** 2) / (2 * 12.0 ** 2) + (dy ** 2) / (2 * 14.0 ** 2)))
        col = col * (1 - 0.55 * g[:, None]) + np.array((255, 196, 130), np.float32) * 0.55 * g[:, None] * (0.7 + 0.3 * n[:, None])
        far = np.clip(1 - dy / 5.0, 0, 1) * 0.7
        col = col * (1 - far) + np.array((205, 212, 228), np.float32) * far
        a[y] = col
    sd = np.sqrt((xx - sunx) ** 2 + (yy - (hz - 0.4)) ** 2)
    a[sd < 1.7] = (255, 240, 196)
    return img_of(a + np.random.RandomState(8).uniform(-1.2, 1.2, (h, w))[..., None])


def view_descent():
    w, h = 32, 48
    rnd = random.Random(36006)
    n = vnoise(w, h, 14, 11, 12) * 0.6 + vnoise(w, h, 6, 5, 13) * 0.4
    a = vgrad(w, h, [(0, (134, 138, 146)), (0.6, (160, 164, 170)), (1, (178, 182, 188))])
    a += ((n - 0.5) * 34)[..., None]
    img = img_of(a)
    o = Ov(w, h, 8)
    for _ in range(46):
        x, y = rnd.uniform(-6, 36), rnd.uniform(-4, 48)
        ln = rnd.uniform(5, 10)
        col = rnd.choice([(204, 208, 216), (196, 200, 208), (120, 124, 134), (210, 214, 220)])
        o.line([(x, y), (x - ln * 0.36, y + ln)], col, 0.55)
    o.apply(img)
    o = Ov(w, h, 8)
    for x, y, r in ((9, 14, 1.9), (22, 10, 1.4), (14, 30, 2.2), (25, 36, 1.7), (7, 40, 1.3), (20, 22, 1.2),
                    (17, 41, 1.0), (27, 20, 1.0)):
        o.ell(x, y + 0.2, r + 0.55, r + 0.65, (98, 104, 116))
        o.ell(x, y, r, r + 0.1, (196, 204, 214))
        o.ell(x - r * 0.3, y - r * 0.4, max(0.45, r * 0.35), max(0.45, r * 0.35), (248, 250, 252))
        o.line([(x, y + r), (x + 0.1, y + r + rnd.uniform(1.5, 4))], (150, 156, 168), 0.5)
    o.apply(img)
    return img


def view_ground():
    w, h = 32, 48
    hz = 21
    a = np.zeros((h, w, 3), np.float32)
    a[:hz] = vgrad(w, hz, [(0, (18, 24, 46)), (1, (50, 60, 88))])
    a[hz:] = vgrad(w, h - hz, [(0, (34, 40, 56)), (1, (18, 22, 32))])
    wet = vnoise(w, h, 3, 6, 21)
    a[hz:] += ((wet[hz:] - 0.5) * 14)[..., None]
    img = img_of(a)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 18, 10, hz - 1], fill=(30, 36, 54))
    d.rectangle([17, 17, 31, hz - 1], fill=(28, 34, 52))
    d.rectangle([20, 14, 22, 17], fill=(32, 38, 58))
    rnd = random.Random(36007)
    for x in list(range(0, 11)) + list(range(17, 32)):
        if rnd.random() < 0.55:
            px(img, x, rnd.choice([19, 20]), rnd.choice([(255, 226, 150), (240, 240, 230), (255, 190, 100)]))
    px(img, 21, 14, (255, 70, 60))
    lights = []
    for s_ in (0.03, 0.08, 0.15, 0.25, 0.4, 0.6, 0.88):
        y = hz + 0.8 + 26.5 * s_
        for sign in (-1, 1):
            lights.append((16 + sign * 15 * s_ - 0.5 * s_, y, 0.35 + 0.95 * s_, (70, 130, 255)))
        lights.append((16 + 3.2 * s_, y + 0.6 * s_, 0.3 + 0.8 * s_, (70, 255, 130)))
    refl = Ov(w, h, 4)
    for x, y, r, col in lights:
        L = 2 + r * 6
        for i in range(int(L * 2)):
            t = i / (L * 2)
            refl.rect(x - r * 0.5, y + r + i * 0.5, x + r * 0.5, y + r + i * 0.5 + 0.5, mixc(col, (22, 26, 38), t * 0.85))
    for x in range(0, 11, 2):
        refl.rect(x, hz + 1, x + 0.7, hz + 5, (92, 78, 56))
    for x in range(18, 32, 3):
        refl.rect(x, hz + 1, x + 0.7, hz + 4, (84, 74, 58))
    refl.apply(img)
    o = Ov(w, h, 8)
    for x, y, r, col in lights:
        o.ell(x, y, r * 1.9, r * 1.9, mixc((24, 28, 42), col, 0.35))
    o.apply(img)
    o = Ov(w, h, 8)
    for x, y, r, col in lights:
        o.ell(x, y, r, r, col)
    o.apply(img)
    return img


# ------------------------------------------------------------------ signs

def pict_nosmoking(o, box, ring, bar, cig, tip):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0

    def P(u, v):
        return (x0 + u * w, y0 + v * h)
    cx, cy = P(0.5, 0.5)
    o.ring(cx, cy, w * 0.46, w * 0.09, ring)
    a, b = P(0.18, 0.5), P(0.62, 0.5)
    o.rect(a[0], cy - h * 0.065, b[0], cy + h * 0.075, cig)
    o.rect(a[0], cy - h * 0.065, P(0.32, 0)[0], cy + h * 0.075, tip)
    o.line([P(0.72, 0.46), P(0.68, 0.36), P(0.74, 0.26)], cig, w * 0.05)
    o.line([P(0.76, 0.5), P(0.82, 0.4)], cig, w * 0.04)
    o.line([P(0.19, 0.19), P(0.81, 0.81)], bar, w * 0.10)


def pict_belt(o, box, col, hole):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0

    def P(u, v):
        return (x0 + u * w, y0 + v * h)
    o.poly([P(0.0, 0.62), P(0.0, 0.40), P(0.40, 0.32), P(0.40, 0.56)], col)
    o.poly([P(1.0, 0.62), P(1.0, 0.40), P(0.60, 0.32), P(0.60, 0.56)], col)
    a, b = P(0.34, 0.28), P(0.66, 0.72)
    o.rrect(a[0], a[1], b[0], b[1], w * 0.07, col)
    c, e = P(0.43, 0.38), P(0.57, 0.62)
    o.rrect(c[0], c[1], e[0], e[1], w * 0.03, hole)
    f, g = P(0.46, 0.45), P(0.54, 0.74)
    o.rect(f[0], f[1], g[0], g[1], col)


def psu(lit):
    img = flat(32, 16, CHAR, 1.2, 36010 + lit)
    img = bevel(img, (0, 0, 32, 16), 0.25 if lit else 0.15, 0.3)
    A, B = (1, 1, 15, 15), (17, 1, 31, 15)
    if lit:
        h = Ov(32, 16, 8)
        pict_nosmoking(h, A, WHITE, WHITE, WHITE, WHITE)
        pict_belt(h, B, WHITE, WHITE)
        m = h.alpha().filter(ImageFilter.GaussianBlur(2.2))
        img.paste(Image.new("RGB", (32, 16), (255, 226, 170)), (0, 0), m.point(lambda v: int(v * 0.55)))
        o = Ov(32, 16, 8)
        pict_nosmoking(o, A, (255, 52, 42), (255, 52, 42), WHITE, (255, 190, 90))
        pict_belt(o, B, WHITE, CHAR)
        o.apply(img)
    else:
        o = Ov(32, 16, 8)
        g = (84, 86, 92)
        pict_nosmoking(o, A, g, g, g, g)
        pict_belt(o, B, g, CHAR)
        o.apply(img)
    return img


def sign_exit():
    w, h = 32, 16
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    f = 1.0 - 0.16 * (((xx - 15.5) / 16) ** 2 + ((yy - 7.5) / 8) ** 2)
    a = np.empty((h, w, 3), np.float32)
    a[:] = (0, 160, 80)
    a *= f[..., None]
    img = img_of(a + np.random.RandomState(36011).uniform(-1, 1, (h, w))[..., None])
    outline(img, 1, 1, 31, 15, (120, 232, 160))
    text(img, "EXIT", (3, 3, 29, 13), WHITE, DIN, 14)
    return img


def placard_flightdeck():
    img = flat(32, 8, (66, 68, 72), 1.2, 36012)
    img = bevel(img, (0, 0, 32, 8), 0.2, 0.3)
    draw_text(img, "FLIGHT", 0, 1, WHITE, F3, 1, 0)
    draw_text(img, "DECK", 19, 1, WHITE, F3, 1, 0)
    rect(img, 2, 6, 30, 7, (255, 200, 80))
    return img


def man(o, box, col):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0

    def P(u, v):
        return (x0 + u * w, y0 + v * h)
    o.ell(*P(0.5, 0.09), w * 0.14, w * 0.14, col)
    a, b = P(0.22, 0.24), P(0.78, 0.60)
    o.rrect(a[0], a[1], b[0], b[1], w * 0.09, col)
    for u0, u1 in ((0.04, 0.17), (0.83, 0.96)):
        a, b = P(u0, 0.26), P(u1, 0.60)
        o.rrect(a[0], a[1], b[0], b[1], w * 0.06, col)
    for u0, u1 in ((0.27, 0.47), (0.53, 0.73)):
        a, b = P(u0, 0.58), P(u1, 1.0)
        o.rrect(a[0], a[1], b[0], b[1], w * 0.06, col)


def woman(o, box, col):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0

    def P(u, v):
        return (x0 + u * w, y0 + v * h)
    o.ell(*P(0.5, 0.09), w * 0.14, w * 0.14, col)
    o.poly([P(0.34, 0.23), P(0.66, 0.23), P(0.94, 0.70), P(0.06, 0.70)], col)
    for u0, u1 in ((0.30, 0.45), (0.55, 0.70)):
        a, b = P(u0, 0.66), P(u1, 1.0)
        o.rrect(a[0], a[1], b[0], b[1], w * 0.05, col)
    for u0, u1 in ((0.14, 0.26), (0.74, 0.86)):
        a, b = P(u0, 0.28), P(u1, 0.56)
        o.rrect(a[0], a[1], b[0], b[1], w * 0.05, col)


def sign_lav():
    w, h = 32, 16
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    f = 1.0 + 0.1 * (1 - ((xx - 15.5) / 16) ** 2)
    a = np.empty((h, w, 3), np.float32)
    a[:] = (50, 54, 60)
    img = img_of(a * f[..., None] + np.random.RandomState(36013).uniform(-1, 1, (h, w))[..., None])
    img = bevel(img, (0, 0, 32, 16), 0.2, 0.25)
    for y in range(2, 14):
        px(img, 16, y, (98, 102, 108))
    o = Ov(w, h, 8)
    man(o, (3.5, 2, 13.5, 14), (242, 246, 242))
    woman(o, (18.5, 2, 28.5, 14), (242, 246, 242))
    o.apply(img)
    return img


def indicator(label, col, hi):
    w, h = 16, 8
    img = flat(w, h, col, 1.2, 36014 + len(label) + col[0])
    outline(img, 0, 0, w, h, scale(col, 0.55))
    outline(img, 1, 1, w - 1, h - 1, hi)
    pix_text(img, label, 8, 1, WHITE, F3, 1)
    return img


def placard_lifevest():
    w, h = 32, 8
    img = flat(w, h, (236, 236, 228), 1.2, 36016)
    outline(img, 0, 0, w, h, (140, 144, 148))
    o = Ov(w, h, 8)
    o.poly([(1.3, 1.2), (3.2, 1.2), (4.2, 2.6), (5.2, 1.2), (7.2, 1.2), (7.8, 6.6), (0.6, 6.6)], (255, 200, 20),
           outline=(60, 54, 30), width=0.22)
    o.poly([(3.2, 1.2), (4.2, 3.6), (5.2, 1.2), (4.8, 1.2), (4.2, 2.4), (3.6, 1.2)], (236, 236, 228))
    o.rect(1.4, 5.2, 7.0, 5.9, (60, 54, 30))
    o.rect(9.2, 1.0, 10.8, 4.2, (40, 42, 47))
    o.poly([(7.8, 4.0), (12.2, 4.0), (10.0, 6.8)], (40, 42, 47))
    o.apply(img)
    pix_text(img, "UNDER", 22, 1, (40, 42, 47), F3, 1)
    rect(img, 13, 6, 31, 7, (255, 200, 20))
    return img


def placard_exitrow():
    w, h = 32, 16
    img = flat(w, h, (255, 192, 44), 1.2, 36017)
    outline(img, 0, 0, w, h, (60, 48, 20))
    outline(img, 1, 1, w - 1, h - 1, (255, 222, 120))
    shapes(img, lambda d, k: pict_runner(d, (2 * k, 3 * k, 13 * k, 14 * k), 255), (30, 32, 36))
    text(img, "EXIT\nROW", (14, 2, 30, 14), (30, 32, 36), DIN, 7)
    return img


def pict_brace(o, box, col):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0

    def P(u, v):
        return (x0 + u * w, y0 + v * h)
    o.line([P(0.08, 0.1), P(0.08, 0.95)], col, w * 0.09)
    o.line([P(0.08, 0.95), P(0.95, 0.95)], col, w * 0.09)
    o.ell(*P(0.58, 0.30), w * 0.11, w * 0.11, col)
    o.line([P(0.38, 0.32), P(0.50, 0.55)], col, w * 0.11)
    o.line([P(0.50, 0.55), P(0.72, 0.62)], col, w * 0.10)
    o.line([P(0.72, 0.62), P(0.86, 0.86)], col, w * 0.10)
    o.line([P(0.45, 0.58), P(0.62, 0.72)], col, w * 0.08)


def pict_vest(o, box, col, ink):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0

    def P(u, v):
        return (x0 + u * w, y0 + v * h)
    o.poly([P(0.1, 0.1), P(0.38, 0.1), P(0.5, 0.36), P(0.62, 0.1), P(0.9, 0.1), P(0.98, 0.9), P(0.02, 0.9)], col,
           outline=ink, width=0.07 * w / 8)
    o.poly([P(0.38, 0.1), P(0.5, 0.36), P(0.62, 0.1), P(0.55, 0.1), P(0.5, 0.22), P(0.45, 0.1)], (240, 240, 236))


def placard_safety():
    w, h = 32, 32
    img = flat(w, h, (238, 238, 232), 1.2, 36018)
    outline(img, 0, 0, w, h, (150, 154, 158))
    rect(img, 1, 1, 31, 13, TEAL)
    pix_text(img, "LIMINAL", 16, 2, WHITE, F3, 1)
    pix_text(img, "AIR", 16, 8, WHITE, F3, 1)
    rect(img, 1, 13, 31, 14, AMBER)
    o = Ov(w, h, 8)
    panels = [(2, 15), (12, 15), (22, 15)]
    ink = (30, 36, 60)
    for x, y in panels:
        o.rrect(x, y, x + 8, y + 12, 0.8, (252, 252, 250), outline=(60, 70, 96), width=0.45)
    pict_belt(o, (3.0, 17.8, 9.0, 24.0), ink, (252, 252, 250))
    pict_brace(o, (13.0, 16.6, 19.0, 25.0), ink)
    pict_vest(o, (23.0, 16.6, 29.0, 25.0), (255, 200, 20), (60, 54, 30))
    o.apply(img)
    for x, y in panels:
        rect(img, x + 1, y + 10, x + 7, y + 11, (166, 170, 176))
    rect(img, 2, 29, 30, 30, TEAL)
    return img


def safetycard():
    w, h = 16, 24
    img = flat(w, h, (244, 244, 240), 1.0, 36019)
    outline(img, 0, 0, w, h, (160, 164, 168))
    rect(img, 0, 0, w, 7, TEAL)
    pix_text(img, "SAFE", 8, 1, WHITE, F3, 1)
    rect(img, 0, 7, w, 8, AMBER)
    shapes(img, lambda d, k: pict_plane(d, (3 * k, 10 * k, 13 * k, 22 * k), 255), (50, 80, 120))
    px(img, 3, 15, (60, 180, 100))
    px(img, 12, 15, (60, 180, 100))
    px(img, 7, 11, (200, 50, 50))
    return img


def magazine():
    w, h = 16, 24
    img = flat(w, h, (200, 178, 70), 1.0, 36020)
    o = Ov(w, h, 8)
    vx, vy = 8, 18.5
    o.poly([(0, 12), (16, 12), (vx + 3, vy - 2), (vx - 3, vy - 2)], (226, 214, 150))
    o.poly([(0, 24), (16, 24), (vx + 3, vy + 2), (vx - 3, vy + 2)], (150, 118, 54))
    o.poly([(0, 12), (vx - 3, vy - 2), (vx - 3, vy + 2), (0, 24)], (206, 182, 72))
    o.poly([(16, 12), (vx + 3, vy - 2), (vx + 3, vy + 2), (16, 24)], (190, 166, 62))
    o.rect(vx - 3, vy - 2, vx + 3, vy + 2, (120, 100, 40))
    o.rect(vx - 1.4, vy - 0.8, vx + 1.4, vy + 2, (70, 60, 30))
    for t in (0.0, 0.3, 0.55, 0.75):
        y0 = 13 + t * 4
        wd = 3.0 * (1 - t) + 0.8
        o.rect(vx - wd, y0, vx + wd, y0 + 1.0 * (1 - t) + 0.4, (255, 255, 240))
    o.apply(img)
    rect(img, 0, 0, w, 12, TEAL)
    pix_text(img, "LIMI", 8, 1, WHITE, F3, 1)
    pix_text(img, "NAL", 8, 7, WHITE, F3, 1)
    rect(img, 0, 12, w, 13, AMBER)
    rect(img, 1, 21, 9, 22, (250, 250, 244))
    rect(img, 1, 23, 6, 24, (250, 250, 244))
    return img


# ------------------------------------------------------------------ doors / skin

def glass_disc(img, cx, cy, r, ring, ring_r):
    W, H = img.size
    o = Ov(W, H, 8)
    o.ell(cx, cy, ring_r, ring_r, ring)
    o.apply(img)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    t = np.clip(((xx - cx) * 0.6 + (yy - cy) * 0.8) / (2 * r) + 0.5, 0, 1)
    a = np.empty((H, W, 3), np.float32)
    a[:] = (60, 72, 90)
    a *= 1.25 - 0.45 * t[..., None]
    streak = np.clip(1 - np.abs((xx - cx) - (cy - yy) * 0.9 - 1.0) / 1.2, 0, 1) * np.clip(1 - np.hypot(xx - cx, yy - cy) / (r + 0.5), 0, 1)
    a += streak[..., None] * 60
    o = Ov(W, H, 8)
    o.ell(cx, cy, r, r, (255, 255, 255))
    o.apply_src(img, img_of(a))
    px(img, cx - 2, cy - 2, (170, 188, 210))
    px(img, cx - 3, cy - 1, (140, 160, 184))


def door_lining():
    w, h = 32, 64
    a = arr(flat(w, h, PLASTIC, 1.4, 36021))
    a[:48, 2] *= 0.94
    a[:48, 3] *= 1.02
    a[:48, 29] *= 0.94
    a[:48, 28] *= 1.02
    a[11, :] *= 0.95
    a[12, :] *= 1.02
    a[:48, 0] *= 0.93
    a[:48, 31] *= 0.93
    img = img_of(a)
    glass_disc(img, 16, 20, 4, (200, 198, 190), 5.2)
    rect(img, 6, 31, 26, 37, (176, 174, 166))
    rect(img, 6, 31, 26, 32, (130, 128, 122))
    rect(img, 6, 31, 7, 37, (146, 144, 138))
    rect(img, 6, 36, 26, 37, (208, 206, 198))
    rect(img, 8, 33, 24, 35, (160, 158, 150))
    outline(img, 21, 24, 28, 29, (178, 176, 168))
    rect(img, 22, 25, 27, 28, RED)
    px(img, 22, 25, (255, 130, 120))
    px(img, 23, 25, (255, 100, 90))
    rect(img, 4, 40, 14, 46, (248, 248, 244))
    outline(img, 4, 40, 14, 46, (200, 30, 30))
    rect(img, 5, 41, 13, 43, (200, 30, 30))
    for x in range(6, 12):
        px(img, x, 44, (200, 30, 30))
    px(img, 10, 43, (248, 248, 244))
    px(img, 11, 45, (200, 30, 30)) if False else None
    yy = np.arange(48, 64, dtype=np.float32)
    a = np.zeros((16, 32, 3), np.float32)
    a[:] = np.array((150, 152, 156), np.float32)
    a *= (1.08 - 0.22 * ((yy - 48) / 16))[:, None, None]
    a += np.random.RandomState(36022).uniform(-1.6, 1.6, (16, 32))[..., None]
    a[0] = (118, 120, 124)
    a[1] *= 1.12
    a[:, 0] *= 0.85
    a[:, 31] *= 0.85
    a[7] = (112, 114, 118)
    a[8] *= 1.1
    img.paste(img_of(a), (0, 48))
    for y in (60, 61, 62):
        for x in range(32):
            px(img, x, y, (250, 200, 20) if ((x + y) // 3) % 2 == 0 else (24, 24, 26))
    for x in range(32):
        px(img, x, 63, (104, 106, 110))
    return img


def door_skin():
    w, h = 32, 64
    a = arr(flat(w, h, SKIN, 1.2, 36023))
    a[:, 0] *= 0.95
    a[:, 31] *= 0.95
    a[9, :] *= 0.95
    a[10, :] *= 1.02
    a[53, :] *= 0.95
    a[54, :] *= 1.02
    img = img_of(a)
    for y in (6, 12, 56, 59):
        for x in range(3, 32, 4):
            px(img, x, y, (212, 216, 220))
    for x in range(2, 30):
        if (x // 3) % 2 == 0:
            rect(img, x, 3, x + 1, 5, (200, 40, 40))
    rect(img, 0, 30, 32, 36, TEAL)
    rect(img, 0, 30, 32, 31, (40, 124, 150))
    rect(img, 0, 37, 32, 38, AMBER)
    glass_disc(img, 16, 20, 4, (176, 182, 188), 5.0)
    outline(img, 9, 40, 23, 45, (200, 30, 30))
    for x in range(12, 19):
        px(img, x, 42, (200, 30, 30))
    px(img, 17, 41, (200, 30, 30))
    px(img, 17, 43, (200, 30, 30))
    px(img, 18, 42, (200, 30, 30))
    return img


def skin_base(seed, seam_y, rivet_ys):
    w = h = 32
    r = np.random.RandomState(seed)
    a = np.empty((h, w, 3), np.float32)
    a[:] = SKIN
    a += r.uniform(-1.0, 1.0, (h, w))[..., None]
    a += np.sin(np.arange(h) / h * 2 * math.pi * 2)[:, None, None] * 1.2
    for y in seam_y:
        a[y % h, :] *= 0.955
        a[(y + 1) % h, :] *= 1.02
    for x in (0, 16):
        a[:, x] *= 0.96
        a[:, (x + 1) % w] *= 1.015
    for y in rivet_ys:
        for x in range(2, w, 4):
            a[y % h, x] *= 0.92
    return img_of(a)


def skin():
    return skin_base(36024, (15,), (12, 18))


def skin_band():
    img = skin_base(36025, (6, 27), (4, 8, 25, 29))
    rect(img, 0, 14, 32, 20, TEAL)
    rect(img, 0, 14, 32, 15, (40, 124, 150))
    rect(img, 0, 21, 32, 22, AMBER)
    return img


def canopy():
    w, h = 32, 32
    r = np.random.RandomState(36026)
    xs = np.arange(w, dtype=np.float32)
    tri = 1 - np.abs(((xs / (w / 5.0)) % 1.0) * 2 - 1)      # five folds across 32 px (6.4 px each), tiles
    a = np.empty((h, w, 3), np.float32)
    a[:] = (44, 44, 46)
    a *= (1 + (tri - 0.5) * 2 * 0.62)[None, :, None]
    a += r.uniform(-1.5, 1.5, (h, w))[..., None]
    a += np.sin(np.arange(h) / h * 2 * math.pi)[:, None, None] * 1.5
    a[::2, :] *= 0.985
    return img_of(a)


# ------------------------------------------------------------------ galley

ALU = (178, 182, 186)
STEEL = (168, 172, 176)
FRAME = (110, 114, 120)


def galley_cart():
    w, h = 16, 32
    img = brushed(w, h, ALU, 36030, 3.0, horizontal=False)
    img = bevel(img, (0, 0, 16, 32), 0.12, 0.22)
    outline(img, 1, 1, 15, 31, FRAME)
    rect(img, 2, 2, 14, 3, (196, 200, 204))
    rect(img, 3, 9, 6, 23, (110, 114, 120))
    rect(img, 4, 10, 5, 22, (70, 74, 80))
    rect(img, 6, 9, 7, 23, (206, 210, 214))
    rect(img, 8, 4, 14, 7, (150, 24, 24))
    rect(img, 9, 4, 13, 6, (220, 44, 40))
    rect(img, 9, 4, 13, 5, (255, 110, 100))
    rect(img, 9, 10, 14, 16, (250, 250, 246))
    outline(img, 9, 10, 14, 16, (120, 124, 130))
    rect(img, 10, 12, 13, 13, (190, 194, 198))
    rect(img, 10, 14, 12, 15, (190, 194, 198))
    rect(img, 3, 25, 13, 29, TEAL)
    rect(img, 4, 26, 8, 27, WHITE)
    rect(img, 9, 26, 12, 27, AMBER)
    return img


def galley_oven():
    w, h = 32, 32
    img = brushed(w, h, STEEL, 36031, 3.0)
    img = bevel(img, (0, 0, 32, 32), 0.15, 0.22)
    rect(img, 2, 5, 25, 30, (96, 100, 106))
    rect(img, 3, 6, 24, 29, (20, 26, 32))
    a = arr(img)
    yy, xx = np.mgrid[0:32, 0:32].astype(np.float32)
    d = np.clip(1 - np.abs((xx - 5) - (yy - 6) * 0.8 - 6) / 3.0, 0, 1) * ((xx > 3) & (xx < 24) & (yy > 6) & (yy < 29))
    a += d[..., None] * 26
    img = img_of(a)
    for y in (13, 18, 23):
        rect(img, 4, y, 23, y + 1, (62, 68, 76))
        rect(img, 4, y + 1, 23, y + 2, (30, 36, 44))
    for x in (7, 20):
        rect(img, x, 8, x + 1, 28, (34, 40, 48))
    rect(img, 3, 2, 24, 5, (88, 92, 98))
    rect(img, 4, 2, 23, 4, (214, 218, 222))
    rect(img, 4, 3, 23, 4, (176, 180, 186))
    rect(img, 26, 3, 31, 30, (38, 40, 44))
    outline(img, 26, 3, 31, 30, (92, 96, 102))
    rect(img, 27, 5, 31, 8, (10, 30, 16))
    rect(img, 27, 5, 30, 7, (70, 255, 120))
    px(img, 28, 6, (10, 70, 30))
    px(img, 29, 5, (10, 70, 30))
    for i in range(4):
        rect(img, 27, 11 + i * 4, 30, 13 + i * 4, (150, 154, 160))
        px(img, 29 if i == 0 else 27, 10 + i * 4, (255, 200, 60) if i % 2 else (90, 255, 130))
    return img


def galley_coffee():
    w, h = 32, 32
    img = brushed(w, h, STEEL, 36032, 3.0)
    img = bevel(img, (0, 0, 32, 32), 0.15, 0.22)
    rect(img, 3, 3, 29, 10, (36, 38, 42))
    outline(img, 3, 3, 29, 10, (96, 100, 106))
    for x in (6, 12):
        rect(img, x, 5, x + 4, 8, (170, 174, 180))
        rect(img, x, 7, x + 4, 8, (110, 114, 120))
    rect(img, 20, 5, 22, 7, (255, 56, 46))
    rect(img, 24, 5, 26, 7, (70, 255, 120))
    px(img, 21, 5, (255, 170, 160))
    px(img, 25, 5, (190, 255, 200))
    rect(img, 4, 12, 28, 30, (90, 94, 100))
    rect(img, 5, 13, 27, 29, (24, 24, 28))
    rect(img, 5, 13, 27, 14, (12, 12, 14))
    rect(img, 5, 28, 27, 29, (110, 114, 120))
    o = Ov(w, h, 8)
    o.rrect(10.5, 17.5, 21.5, 27.8, 1.2, (206, 224, 232))
    o.rect(10.5, 22.2, 21.5, 27.8, (96, 54, 26))
    o.rect(10.5, 22.2, 21.5, 23.0, (150, 94, 50))
    o.rect(9.8, 16.0, 22.2, 17.8, (14, 14, 16))
    o.rect(14, 14.8, 18, 16.2, (14, 14, 16))
    o.ring(23.4, 21.8, 2.1, 1.1, (14, 14, 16))
    o.rect(21.0, 18.8, 22.0, 24.6, (14, 14, 16))
    o.rect(11.2, 18.2, 12.0, 21.8, (250, 252, 255))
    o.apply(img)
    return img


def galley_stow():
    w, h = 32, 16
    img = brushed(w, h, ALU, 36033, 3.0)
    for x0 in (0, 16):
        img = bevel(img, (x0, 0, x0 + 16, 16), 0.15, 0.22)
        outline(img, x0 + 1, 1, x0 + 15, 15, FRAME)
        rect(img, x0 + 2, 2, x0 + 14, 3, (198, 202, 206))
        rect(img, x0 + 6, 3, x0 + 10, 7, (70, 74, 80))
        rect(img, x0 + 7, 4, x0 + 9, 6, (196, 200, 204))
        px(img, x0 + 8, 4, (255, 255, 255))
        rect(img, x0 + 3, 9, x0 + 13, 14, (248, 248, 244))
        outline(img, x0 + 3, 9, x0 + 13, 14, (140, 144, 150))
        rect(img, x0 + 4, 11, x0 + 12, 12, (188, 192, 198))
    rect(img, 15, 1, 17, 15, (88, 92, 98))
    return img


def galley_waste():
    w, h = 16, 32
    img = brushed(w, h, ALU, 36034, 3.0, horizontal=False)
    img = bevel(img, (0, 0, 16, 32), 0.12, 0.22)
    outline(img, 1, 1, 15, 31, FRAME)
    rect(img, 2, 3, 14, 14, (130, 134, 140))
    rect(img, 3, 4, 13, 13, (150, 154, 160))
    rect(img, 3, 4, 13, 5, (206, 210, 214))
    rect(img, 3, 12, 13, 13, (110, 114, 120))
    pix_text(img, "WASTE", 8, 7, (30, 32, 36), F3, 0)
    for x in (3, 12):
        for y in range(14, 18, 2):
            px(img, x, y, (70, 74, 80))
    rect(img, 4, 25, 12, 29, (70, 74, 80))
    rect(img, 4, 25, 12, 27, (210, 214, 218))
    rect(img, 4, 27, 12, 28, (150, 154, 160))
    return img


def panel_attendant():
    w, h = 32, 32
    img = flat(w, h, (60, 62, 66), 1.2, 36035)
    img = bevel(img, (0, 0, 32, 32), 0.2, 0.3)
    rect(img, 3, 3, 19, 13, (14, 20, 24))
    rect(img, 4, 4, 18, 12, (30, 150, 170))
    for i, wd in enumerate((10, 6, 12, 8)):
        rect(img, 5, 5 + i * 2, 5 + wd, 6 + i * 2, (170, 244, 250) if i else (240, 255, 255))
    cols = [(255, 56, 46), (70, 255, 120), (255, 200, 60), (230, 240, 250)]
    for r_ in range(3):
        for c in range(4):
            x, y = 3 + c * 4, 16 + r_ * 5
            px(img, x + 1, y, cols[(c + r_) % 4])
            rect(img, x, y + 1, x + 3, y + 4, (140, 144, 150) if (c + r_) % 2 else (116, 120, 126))
            rect(img, x, y + 1, x + 3, y + 2, (190, 194, 200))
    rect(img, 22, 3, 30, 30, (36, 38, 42))
    outline(img, 22, 3, 30, 30, (92, 96, 102))
    o = Ov(w, h, 8)
    o.rrect(23.6, 5, 28.4, 25, 1.4, (16, 16, 18))
    o.rrect(23.0, 5, 29.0, 8.4, 1.2, (24, 24, 28))
    o.rrect(23.0, 21.4, 29.0, 25, 1.2, (24, 24, 28))
    o.rect(25.2, 9, 26.8, 20, (52, 54, 60))
    o.line([(25.0, 25.5), (27.5, 26.5), (25.0, 27.5), (27.5, 28.5)], (20, 20, 22), 0.5)
    o.apply(img)
    px(img, 24, 6, (110, 114, 122))
    return img


# ------------------------------------------------------------------ soft things

def curtain():
    w, h = 32, 32
    r = np.random.RandomState(36040)
    xs = np.arange(w, dtype=np.float32)
    pleat = np.cos(((xs / 8.0) % 1.0) * 2 * math.pi) * 0.5 + 0.5
    a = np.empty((h, w, 3), np.float32)
    a[:] = NAVY
    a *= (0.72 + 0.5 * pleat)[None, :, None]
    yy, xx = np.mgrid[0:h, 0:w]
    mx, my = (xx % 8) - 4, (yy % 8) - 4
    m = ((np.abs(mx) + np.abs(my)) <= 1) & (((xx // 8) + (yy // 8)) % 2 == 0)
    a[m] = a[m] * 0.55 + np.array(TEAL, np.float32) * 0.45 * (0.8 + 0.4 * pleat[xx[m]])[:, None] + 6
    a += r.uniform(-2.0, 2.0, (h, w))[..., None]
    return img_of(a)


def blanket():
    w, h = 32, 32
    r = np.random.RandomState(36041)
    a = np.empty((h, w, 3), np.float32)
    a[:] = (70, 96, 150)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    a += ((vnoise(w, h, 6, 6, 3) - 0.5) * 12)[..., None]
    a += r.uniform(-4.5, 4.5, (h, w))[..., None]
    a *= (1 - 0.16 * np.exp(-(((yy - 10) + (xx - 16) * 0.18) / 3.2) ** 2))[..., None]
    a *= (1 + 0.07 * np.exp(-(((yy - 14) + (xx - 16) * 0.18) / 3.0) ** 2))[..., None]
    img = img_of(a)
    b = np.empty((6, w, 3), np.float32)
    b[:] = TEAL
    for y in range(6):
        for x in range(w):
            b[y, x] += (((x + y) % 2) * 14 - 7) if y % 2 == 0 else (((x // 2 + y) % 2) * 12 - 6)
    b += r.uniform(-2, 2, (6, w))[..., None]
    img.paste(img_of(b), (0, 26))
    rect(img, 0, 25, 32, 26, (150, 176, 214))
    rect(img, 0, 31, 32, 32, (12, 66, 90))
    return img


def pillow():
    w, h = 32, 32
    r = np.random.RandomState(36042)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    rr = np.sqrt(((xx - 15.5) / 16) ** 2 + ((yy - 15.5) / 16) ** 2)
    shade = 1.0 - 0.14 * np.clip(rr, 0, 1.3) ** 3 - 0.04 * rr
    a = np.empty((h, w, 3), np.float32)
    a[:] = (246, 248, 250)
    a *= shade[..., None]
    for cx, cy in ((0, 0), (31, 0), (0, 31), (31, 31)):
        d = np.hypot(xx - cx, yy - cy)
        ang = np.arctan2(yy - cy, xx - cx)
        wr = (np.sin(ang * 14) * 0.5 + 0.5) * np.clip(1 - d / 8.0, 0, 1)
        a *= (1 - 0.07 * wr)[..., None]
    a += r.uniform(-1.2, 1.2, (h, w))[..., None]
    sh = (1.0 - 0.1 * np.clip(rr, 0, 1.2) ** 2)[..., None]
    for y0, y1, col in ((13, 19, TEAL), (19, 20, (30, 110, 138)), (21, 22, AMBER)):
        base = np.empty((y1 - y0, w, 3), np.float32)
        base[:] = col
        a[y0:y1] = base * sh[y0:y1] * (1 + 0.08 * np.sin(xx[y0:y1] / 5.0)[..., None])
    return img_of(a)


ROWS = [10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]


def rownums():
    img = Image.new("RGB", (64, 64), (210, 210, 206))
    for i, n in enumerate(ROWS):
        cx, cy = (i % 4) * 16, (i // 4) * 16
        s = str(n)
        wd = text_width(s, F5, 1, 1)
        draw_text(img, s, cx + (16 - wd) // 2, cy + 4, (46, 48, 52), F5, 1, 1)
    return img


# ------------------------------------------------------------------ driver

TEXTURES = [
    ("view-apron", (32, 48), view_apron), ("view-roll", (32, 48), view_roll), ("view-climb", (32, 48), view_climb),
    ("view-cruise", (32, 48), view_cruise), ("view-descent", (32, 48), view_descent),
    ("view-ground", (32, 48), view_ground),
    ("sign-psu-off", (32, 16), lambda: psu(0)), ("sign-psu-on", (32, 16), lambda: psu(1)),
    ("sign-exit", (32, 16), sign_exit), ("placard-flightdeck", (32, 8), placard_flightdeck),
    ("sign-lav", (32, 16), sign_lav),
    ("ind-occupied", (16, 8), lambda: indicator("OCC", (212, 36, 34), (255, 120, 110))),
    ("ind-vacant", (16, 8), lambda: indicator("VAC", (0, 150, 74), (110, 232, 150))),
    ("placard-lifevest", (32, 8), placard_lifevest), ("placard-exitrow", (32, 16), placard_exitrow),
    ("placard-safety", (32, 32), placard_safety), ("safetycard", (16, 24), safetycard),
    ("magazine", (16, 24), magazine), ("door-lining", (32, 64), door_lining), ("door-skin", (32, 64), door_skin),
    ("skin", (32, 32), skin), ("skin-band", (32, 32), skin_band), ("canopy", (32, 32), canopy),
    ("galley-cart", (16, 32), galley_cart), ("galley-oven", (32, 32), galley_oven),
    ("galley-coffee", (32, 32), galley_coffee), ("galley-stow", (32, 16), galley_stow),
    ("galley-waste", (16, 32), galley_waste), ("panel-attendant", (32, 32), panel_attendant),
    ("curtain", (32, 32), curtain), ("blanket", (32, 32), blanket), ("pillow", (32, 32), pillow),
    ("rownums", (64, 64), rownums),
]


def textures():
    os.makedirs(OUT, exist_ok=True)
    for name, size, fn in TEXTURES:
        save(fn(), name, size)
    return [(n, s) for n, s, _ in TEXTURES]


def sheet(path, k=8, width=2600):
    f = ImageFont.load_default()
    x, y, rowh = 8, 8, 0
    placed = []
    for name, size, _ in TEXTURES:
        big = Image.open(os.path.join(OUT, name + ".png")).convert("RGB")
        big = big.resize((big.width * k, big.height * k), Image.NEAREST)
        if x + big.width + 8 > width:
            x, y, rowh = 8, y + rowh + 8, 0
        placed.append((x, y, name, big, size))
        x += big.width + 12
        rowh = max(rowh, big.height + 14)
    out = Image.new("RGB", (width, y + rowh + 8), (255, 0, 255))
    d = ImageDraw.Draw(out)
    for x, y, name, big, size in placed:
        out.paste(big, (x, y + 12))
        d.text((x, y), f"{name} {size[0]}x{size[1]}", fill=(255, 255, 255), font=f)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out.save(path)


if __name__ == "__main__":
    textures()
