"""Cuts demo/raw/*.mp4 into one clip per narration line, timed to its voice, and joins them into demo/demo.mp4.

Usage: python3 demo/build.py      (needs ffmpeg, Pillow, demo/voice/*.wav from voice.py, demo/raw from winrec)
Each scene lists windows of the raw recording (seconds); they are sped up evenly to last as long as the voice.
"""
import json, os, subprocess, wave
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RAW, OUT, TMP = (os.path.join(HERE, p) for p in ("raw", "demo.mp4", "raw/build"))
W, H, PAD = 1920, 1080, 0.6  # seconds of silence after each line

SCENES = {  # id: (source, [(start, end), ...], caption)
    "s0_intro": (None, [], "Scope Firewall"),
    "s1_team": ("console", [(8, 50)], "1  One template: 5 agents, 4 rooms"),
    "s2_kickoff": ("discord", [(392, 430), (770, 800), (840, 905)], "2  Kickoff: brief to signed contract"),
    "s3_dates": ("discord", [(905, 935), (1000, 1030)], "3  Dates from real work, accepted by the project manager"),
    "s4_split": ("discord", [(1080, 1125)], "4  One client message, two requests"),
    "s5_verify": ("discord", [(1370, 1405), (1405, 1420)], "5  Two providers verify blind"),
    "s6_plan": ("discord", [(1505, 1532), (1650, 1675), (1745, 1762)], "6  Hotfix, quote, delay proposed"),
    "s7_client": ("discord", [(1860, 1898)], "7  Unexpected delay, client update"),
    "s8_delivery": ("discord", [(1975, 1998), (2050, 2101)], "8  Roles and approvals at delivery"),
    "s9_outro": (None, [], "Humans decide. Tools check. Switch keeps the record."),
}


def font(size):
    for f in ("/System/Library/Fonts/SFNS.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def card(text, sub, path):
    im = Image.new("RGB", (W, H), (24, 26, 32))
    d = ImageDraw.Draw(im)
    d.text((W // 2, H // 2 - 40), text, font=font(84 if len(text) < 30 else 56), fill="white", anchor="mm")
    d.text((W // 2, H // 2 + 60), sub, font=font(40), fill=(170, 180, 200), anchor="mm")
    im.save(path)


def caption(text, path):
    im = Image.new("RGBA", (W, 90), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((30, 15, 60 + d.textlength(text, font=font(40)), 80), 14, fill=(20, 20, 28, 220))
    d.text((45, 47), text, font=font(40), fill="white", anchor="lm")
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
    audio = ["-i", wav, "-af", f"apad=pad_dur={PAD}", "-c:a", "aac", "-ar", "48000", "-ac", "2"]
    fit = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x181a20,fps=30"
    if src is None:
        png = os.path.join(TMP, f"card{i}.png")
        card(text, "Client projects, from kickoff to delivery, on Switch" if i == 0 else "github.com/ru-ji/scope-firewall", png)
        run("-loop", "1", "-i", png, *audio, "-t", f"{dur:.2f}", "-vf", "fps=30,format=yuv420p",
            "-c:v", "libx264", "-shortest", out)
        return out
    cap = os.path.join(TMP, f"cap{i}.png")
    caption(text, cap)
    total = sum(e - s for s, e in windows)
    speed = total / dur
    parts = "".join(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[p{k}];" for k, (s, e) in enumerate(windows))
    joined = "".join(f"[p{k}]" for k in range(len(windows))) + f"concat=n={len(windows)}:v=1:a=0[j];"
    graph = (parts + joined + f"[j]setpts=PTS/{speed:.4f},{fit}[v];[v][2:v]overlay=0:{H - 100},format=yuv420p[o]")
    run("-i", os.path.join(RAW, src + ".mp4"), *audio[:2], "-i", cap, "-filter_complex", graph,
        "-map", "[o]", "-map", "1:a", "-af", f"apad=pad_dur={PAD}", "-c:a", "aac", "-ar", "48000", "-ac", "2",
        "-t", f"{dur:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", out)
    return out


if __name__ == "__main__":
    os.makedirs(TMP, exist_ok=True)
    ids = [l["id"] for l in json.load(open(os.path.join(HERE, "narration.json")))]
    clips = [scene(sid, *SCENES[sid], i) for i, sid in enumerate(ids)]
    lst = os.path.join(TMP, "list.txt")
    open(lst, "w").write("".join(f"file '{c}'\n" for c in clips))
    run("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", OUT)
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", OUT],
                             capture_output=True, text=True).stdout)
    print(f"{OUT}: {d:.1f}s")
    assert d < 180, "over 3 minutes"
