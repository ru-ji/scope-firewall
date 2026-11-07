"""Narration voices with Gemini text-to-speech. Reads GEMINI_API_KEY from the environment or from .env.

Usage: python3 demo/voice.py [scene id ...]     writes demo/voice/<id>.wav for each line of demo/narration.json
Env:   GEMINI_TTS_MODEL (default gemini-2.5-flash-preview-tts), GEMINI_VOICE (default Charon)
"""
import base64, json, os, ssl, sys, time, urllib.error, urllib.request, wave

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.environ.get("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
VOICE = os.environ.get("GEMINI_VOICE", "Charon")


def key():
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    env = os.path.join(HERE, "..", ".env")
    for line in open(env) if os.path.exists(env) else []:
        if line.startswith("GEMINI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("GEMINI_API_KEY is not set (environment or .env)")


def speak(text, path):
    body = {"contents": [{"parts": [{"text": "Read this in a calm, clear product-demo voice: " + text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}}}}
    req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
                                 json.dumps(body).encode(), {"Content-Type": "application/json", "x-goog-api-key": key()})
    cafile = "/etc/ssl/cert.pem" if os.path.exists("/etc/ssl/cert.pem") else None
    for attempt in range(6):  # free-tier keys are rate limited: wait and retry on 429
        try:
            out = json.load(urllib.request.urlopen(req, context=ssl.create_default_context(cafile=cafile), timeout=120))
            break
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 5:
                raise
            time.sleep(30 * (attempt + 1))
    pcm = base64.b64decode(out["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
    with wave.open(path, "wb") as w:  # Gemini returns 16-bit mono PCM at 24 kHz
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm)
    return len(pcm) / 48000


if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "voice"), exist_ok=True)
    lines = json.load(open(os.path.join(HERE, "narration.json")))
    for line in lines:
        if sys.argv[1:] and line["id"] not in sys.argv[1:]:
            continue
        secs = speak(line["text"], os.path.join(HERE, "voice", line["id"] + ".wav"))
        print(f"{line['id']}: {secs:.1f}s")
