"""Cuts demo/raw/*.mp4 into one clip per narration line, timed to its voice, and joins them into demo/demo.mp4.

Usage: python3 demo/build.py      (needs ffmpeg, Pillow, demo/voice/*.wav from voice.py, demo/raw from winrec)
Each scene lists windows of the raw recording (seconds), sped up evenly to last as long as the voice, and shown
as a real macOS window with rounded corners and a soft shadow on a light background, with a short caption and fades between scenes.
"""
import json, os, subprocess, wave
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RAW, OUT, TMP = (os.path.join(HERE, p) for p in ("raw", "demo.mp4", "raw/build"))
W, H, PAD, FADE = 1920, 1080, 0.6, 0.35
BG, INK, MUTED = (245, 245, 247), (29, 29, 31), (134, 134, 139)
# the recording is already a real macOS window (title bar included): it is shown at this height, centred
WY, CH = 128, 900
ASPECT = {"discord": 2848 / 1768, "console": 2800 / 1800}

SCENES = {  # id: (source, [(start, end), ...], caption)
    "s0_intro": (None, [], ("Scope Firewall", "A client project team of AI agents, built on Switch")),
    "s1_team": ("console", [(8, 50)], "One template creates the whole team"),
    "s2_kickoff": ("discord", [(392, 430), (770, 800), (840, 905)], "Kickoff: the brief becomes a contract"),
    "s3_dates": ("discord", [(905, 935), (1000, 1030)], "Dates from real work, accepted by a person"),
    "s4_split": ("discord", [(1080, 1125)], "One client message, two requests"),
    "s5_verify": ("discord", [(1370, 1405), (1405, 1420)], "Two providers verify, blind"),
    "s6_plan": ("discord", [(1505, 1532), (1650, 1675), (1745, 1762)], "A free hotfix, a paid quote, an honest delay"),
    "s7_client": ("discord", [(1860, 1898)], "Every date comes with its reason"),
    "s8_delivery": ("discord", [(1975, 1998), (2050, 2101)], "Only the tech lead can ship"),
    "s9_outro": (None, [], ("Thank you for watching", "Scope Firewall  ·  built on Switch  ·  github.com/ru-ji/scope-firewall")),
}


def font(size, bold=False):
    path = "/System/Library/Fonts/SFNS.ttf"
    f = ImageFont.truetype(path, size)
    try:
        f.set_variation_by_name("Semibold" if bold else "Regular")
    except Exception:
        pass
    return f


def frame(path, ww):
    """Light background and a soft shadow; the window area (rounded corners) is left transparent."""
    wx, r = (W - ww) // 2, 16
    im = Image.new("RGBA", (W, H), BG + (255,))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((wx, WY + 18, wx + ww, WY + CH + 18), r, fill=(0, 0, 0, 80))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(30)))
    hole = Image.new("L", (W, H), 255)
    ImageDraw.Draw(hole).rounded_rectangle((wx, WY, wx + ww - 1, WY + CH - 1), r, fill=0)
    im.putalpha(Image.composite(im.getchannel("A"), Image.new("L", (W, H), 0), hole))
    im.save(path)


def caption(text, path):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((W / 2, WY / 2 + 6), text, font=font(34, True), fill=INK + (255,), anchor="mm")
    im.save(path)


def card(title, sub, path):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((W / 2, H / 2 - 30), title, font=font(84, True), fill=INK, anchor="mm")
    d.text((W / 2, H / 2 + 50), sub, font=font(30), fill=MUTED, anchor="mm")
    im.save(path)


def secs(wav):
    with wave.open(wav) as w:
        return w.getnframes() / w.getframerate()


def run(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


def scene(sid, src, windows, text, i):
    wav = os.path.join(HERE, "voice", sid + ".wav")
    dur = secs(wav) + PAD
    out = os.path.join(TMP, f"{i:02d}.mp4")
    fades = f"fade=in:st=0:d={FADE},fade=out:st={dur - FADE:.2f}:d={FADE}"
    afade = f"apad=pad_dur={PAD},afade=in:st=0:d=0.15,afade=out:st={dur - 0.25:.2f}:d=0.25"
    enc = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-t", f"{dur:.2f}"]
    if src is None:
        png = os.path.join(TMP, f"card{i}.png")
        card(*text, png)
        run("-loop", "1", "-framerate", "30", "-i", png, "-i", wav, "-vf", fades, "-af", afade, *enc, out)
        return out
    cap, frame_png = os.path.join(TMP, f"cap{i}.png"), os.path.join(TMP, f"frame_{src}.png")
    caption(text, cap)
    ww = round(CH * ASPECT[src] / 2) * 2
    frame(frame_png, ww)
    speed = sum(e - s for s, e in windows) / dur
    parts = "".join(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[p{k}];" for k, (s, e) in enumerate(windows))
    graph = (parts + "".join(f"[p{k}]" for k in range(len(windows))) + f"concat=n={len(windows)}:v=1:a=0[j];"
             f"[j]setpts=PTS/{speed:.4f},fps=30,scale={ww}:{CH}:flags=lanczos[v];"
             f"color=c=0x{BG[0]:02x}{BG[1]:02x}{BG[2]:02x}:s={W}x{H}:r=30[bg];"
             f"[bg][v]overlay={(W - ww) // 2}:{WY}:shortest=1[b];[b][2:v]overlay=0:0[c];[c][3:v]overlay=0:0,{fades}[o]")
    run("-i", os.path.join(RAW, src + ".mp4"), "-i", wav, "-loop", "1", "-i", frame_png, "-loop", "1", "-i", cap,
        "-filter_complex", graph, "-map", "[o]", "-map", "1:a", "-af", afade, *enc, out)
    return out


if __name__ == "__main__":
    os.makedirs(TMP, exist_ok=True)
    ids = [l["id"] for l in json.load(open(os.path.join(HERE, "narration.json")))]
    clips = [scene(sid, *SCENES[sid], i) for i, sid in enumerate(ids)]
    lst = os.path.join(TMP, "list.txt")
    open(lst, "w").write("".join(f"file '{c}'\n" for c in clips))
    run("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", OUT)
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", OUT],
                             capture_output=True, text=True).stdout)
    print(f"{OUT}: {d:.1f}s")
    assert d < 180, "over 3 minutes"
