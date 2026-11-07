"""Wraps docs/blog/shot*.png in a macOS style window with a soft shadow on a transparent background, (the diagram is diagram.html, rendered with headless Chrome).

Usage: python3 docs/blog/mockup.py   (Pillow). Reads shotN.png, writes shotN_mock.png and diagram.png.
"""
import glob, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SANS = "/System/Library/Fonts/SFNS.ttf"


def font(size):
    return ImageFont.truetype(SANS, size)


def gradient(w, h, top, bottom):
    g = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(h - 1, 1)
        g.putpixel((0, y), tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)))
    return g.resize((w, h))


def rounded_mask(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    return m


def window(shot, title):
    bar, r = 56, 22
    w, h = shot.width, shot.height + bar
    win = Image.new("RGB", (w, h), (43, 45, 49))
    d = ImageDraw.Draw(win)
    d.rectangle((0, 0, w, bar), fill=(32, 34, 37))
    for i, c in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        x = 28 + i * 30
        d.ellipse((x - 9, bar / 2 - 9, x + 9, bar / 2 + 9), fill=c)
    d.text((w / 2, bar / 2), title, font=font(22), fill=(185, 187, 190), anchor="mm")
    win.paste(shot, (0, bar))
    return win, rounded_mask(w, h, r)


def mock(path):
    """Transparent background with a soft shadow, so the window sits on any page color (Medium light or dark)."""
    shot = Image.open(path).convert("RGB")
    win, mask = window(shot, "Discord  ·  Bug Team Demo")
    pad = 70
    W, H = win.width + 2 * pad, win.height + 2 * pad
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((pad, pad + 18, pad + win.width, pad + win.height + 18), 22,
                                             fill=(0, 0, 0, 110))
    out_im = shadow.filter(ImageFilter.GaussianBlur(26))
    out_im.paste(win.convert("RGBA"), (pad, pad), mask)
    ImageDraw.Draw(out_im).rounded_rectangle((pad, pad, pad + win.width - 1, pad + win.height - 1), 22,
                                             outline=(255, 255, 255, 38), width=2)  # keeps the edge visible on dark pages
    out = path.replace(".png", "_mock.png")
    out_im.resize((1400, H * 1400 // W), Image.LANCZOS).save(out, optimize=True)
    return out


if __name__ == "__main__":
    for p in sorted(glob.glob(os.path.join(HERE, "shot[0-9].png"))):
        print(mock(p))
