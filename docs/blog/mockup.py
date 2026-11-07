"""Wraps docs/blog/shot*.png in a macOS style window on a soft gradient, and draws the workflow diagram.

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
    shot = Image.open(path).convert("RGB")
    win, mask = window(shot, "Discord  ·  Bug Team Demo")
    pad = 110
    W, H = win.width + 2 * pad, win.height + 2 * pad
    bg = gradient(W, H, (122, 108, 236), (236, 130, 172))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((pad, pad + 24, pad + win.width, pad + win.height + 24), 22,
                                             fill=(20, 10, 40, 150))
    bg = Image.alpha_composite(bg.convert("RGBA"), shadow.filter(ImageFilter.GaussianBlur(34)))
    bg.paste(win, (pad, pad), mask)
    out = path.replace(".png", "_mock.png")
    bg.convert("RGB").resize((1400, H * 1400 // W), Image.LANCZOS).save(out, optimize=True)
    return out


def diagram():
    W, H = 2000, 1240
    im = gradient(W, H, (246, 247, 251), (233, 236, 246)).convert("RGBA")
    d = ImageDraw.Draw(im)
    PERSON, AGENT, TOOL = ((255, 243, 224), (240, 160, 60)), ((228, 238, 255), (90, 130, 240)), ((226, 247, 236), (52, 168, 110))

    def card(x, y, w, h, kind, title, sub):
        fill, accent = kind
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((x, y + 8, x + w, y + h + 8), 22, fill=(40, 50, 90, 45))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
        d.rounded_rectangle((x, y, x + w, y + h), 22, fill=(255, 255, 255))
        d.rounded_rectangle((x, y, x + 12, y + h), 6, fill=accent)
        d.text((x + 36, y + h / 2 - 18), title, font=font(30), fill=(25, 28, 40), anchor="lm")
        d.text((x + 36, y + h / 2 + 20), sub, font=font(22), fill=(110, 115, 135), anchor="lm")

    def arrow(x1, y1, x2, y2):
        d.line((x1, y1, x2, y2), fill=(150, 156, 180), width=4)
        d.polygon([(x2, y2), (x2 - 16, y2 - 9), (x2 - 16, y2 + 9)] if x2 > x1 and abs(y2 - y1) < 2 else
                  [(x2, y2), (x2 - 15, y2 - 12), (x2 - 18, y2 + 6)] if y2 < y1 else
                  [(x2, y2), (x2 - 18, y2 - 6), (x2 - 15, y2 + 12)], fill=(150, 156, 180))

    def lane(y, label):
        d.text((90, y), label, font=font(24), fill=(120, 125, 150))

    d.text((W / 2, 80), "One client project, one team chat", font=font(54), fill=(25, 28, 40), anchor="mm")
    d.text((W / 2, 140), "Scope Firewall on Switch: agents do the legwork, people decide, tools check",
           font=font(28), fill=(110, 115, 135), anchor="mm")
    cw, ch, gap, x0 = 400, 120, 70, 90
    xs = [x0 + i * (cw + gap) for i in range(4)]

    lane(210, "KICKOFF")
    row = [(PERSON, "Client brief", "pasted in #planning"), (TOOL, "Signed contract", "rules the app must pass"),
           (TOOL, "Dates proposed", "working days, tests included"), (PERSON, "Project manager", "accepts the date")]
    for x, (k, t, s) in zip(xs, row):
        card(x, 250, cw, ch, k, t, s)
    for x in xs[:-1]:
        arrow(x + cw + 8, 310, x + cw + gap - 8, 310)

    lane(450, "EVERY CLIENT MESSAGE")
    card(xs[0], 540, cw, ch, AGENT, "Reception", "splits it, no code access")
    card(xs[1], 490, cw, ch - 10, AGENT, "Verifier", "Claude Code, #verification")
    card(xs[1], 620, cw, ch - 10, AGENT, "Contradictor", "Codex, blind, #cross-check")
    card(xs[2], 540, cw, ch, AGENT, "Planner", "compares both verdicts")
    card(xs[3], 490, cw, ch - 10, TOOL, "Defect: hotfix", "free, delay proposed")
    card(xs[3], 620, cw, ch - 10, TOOL, "New feature: quote", "billed, next version")
    arrow(xs[0] + cw + 8, 580, xs[1] - 8, 545)
    arrow(xs[0] + cw + 8, 620, xs[1] - 8, 675)
    arrow(xs[1] + cw + 8, 545, xs[2] - 8, 580)
    arrow(xs[1] + cw + 8, 675, xs[2] - 8, 620)
    arrow(xs[2] + cw + 8, 580, xs[3] - 8, 545)
    arrow(xs[2] + cw + 8, 620, xs[3] - 8, 675)

    lane(800, "DELIVERY")
    row = [(TOOL, "Staging", "checked against the contract"), (PERSON, "Tech lead", "the only one who promotes"),
           (TOOL, "Production", "Allow or Decline in the chat"), (PERSON, "Client update", "every date and its reason")]
    for x, (k, t, s) in zip(xs, row):
        card(x, 840, cw, ch, k, t, s)
    for x in xs[:-1]:
        arrow(x + cw + 8, 900, x + cw + gap - 8, 900)

    for i, (k, t) in enumerate([(PERSON, "a person decides"), (AGENT, "an AI agent works"), (TOOL, "a tested tool checks")]):
        x = 520 + i * 360
        d.rounded_rectangle((x, 1080, x + 34, 1114), 9, fill=k[1])
        d.text((x + 50, 1097), t, font=font(26), fill=(60, 64, 85), anchor="lm")
    im.convert("RGB").resize((1600, 992), Image.LANCZOS).save(os.path.join(HERE, "diagram.png"), optimize=True)


if __name__ == "__main__":
    for p in sorted(glob.glob(os.path.join(HERE, "shot[0-9].png"))):
        print(mock(p))
    diagram()
    print("diagram.png")
