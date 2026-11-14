"""Render the synthetic Earth clip and prepare its Mars assets."""
import array
import json
import math
from pathlib import Path
import subprocess
import sys
import wave

from PIL import Image, ImageDraw
import imageio_ffmpeg

source, dest = map(Path, sys.argv[1:])
dest.mkdir(parents=True, exist_ok=True)
with wave.open(str(source)) as wav:
    assert wav.getnchannels() == 1 and wav.getsampwidth() == 2
    rate = wav.getframerate()
    samples = array.array("h", wav.readframes(wav.getnframes()))

portrait = Image.new("RGBA", (320, 360))
d = ImageDraw.Draw(portrait)
d.ellipse((64, 24, 255, 257), fill="#46282c")
d.rounded_rectangle((47, 258, 273, 386), radius=56, fill="#367771")
d.rounded_rectangle((133, 207, 187, 286), radius=22, fill="#c38365")
d.ellipse((87, 54, 233, 242), fill="#e4a47e")
d.pieslice((76, 36, 244, 177), 180, 342, fill="#46282c")
d.arc((150, 145, 176, 181), 55, 135, fill="#ab6d55", width=3)
for x in (110, 196):
    d.ellipse((x, 160, x + 18, 170), fill="#da8b73")
portrait.save(dest / "portrait.png", optimize=True)

frames = []
fps = 20
for i in range(math.ceil(len(samples) / rate * fps)):
    t = i / fps
    chunk = samples[round(i * rate / fps):round((i + 1) * rate / fps)]
    rms = math.sqrt(sum(s*s for s in chunk) / max(1, len(chunk)))
    mouth = min(100, round(rms / 24))
    blink = max([0] + [round(100 * max(0, 1 - abs(t - b) / .16)) for b in (2.2, 5.6, 9.4, 13.5, 17.7, 21.3, 23.8)])
    smile = round(18 + 65 * max([0] + [max(0, 1 - abs(t - s) / 2.3) for s in (1.2, 7, 11.5, 23.5)]))
    tilt = round(5 * math.sin(t * .66))
    frames.append([mouth, blink, smile, tilt])

track = {"stepMs": 50, "channels": ["mouth", "blink", "smile", "tilt"], "frames": frames}
(dest / "motion.json").write_bytes(json.dumps(track, separators=(",", ":")).encode())
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
video = dest / "earth-reference.mp4"
with subprocess.Popen([
    ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo", "-pixel_format", "rgb24",
    "-video_size", "640x440", "-framerate", str(fps), "-i", "-", "-i", str(source),
    "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "96k", "-shortest", "-movflags", "+faststart", str(video)
], stdin=subprocess.PIPE) as encoder:
    for mouth, blink, smile, tilt in frames:
        face = portrait.copy()
        d = ImageDraw.Draw(face)
        for x in (124, 196):
            h = max(1, round(7 * (1 - blink / 100)))
            d.ellipse((x - 9, 144 - h, x + 9, 144 + h), fill="#38242a")
        h = max(2, round(mouth * .19))
        w = round(13 + smile * .19)
        d.ellipse((160 - w, 192 - h, 160 + w, 192 + h), fill="#78363e")
        face = face.rotate(-tilt, resample=Image.Resampling.BICUBIC)
        frame = Image.new("RGB", (640, 440), "#233548")
        frame.paste(face, (160, 49), face)
        ImageDraw.Draw(frame).text((20, 20), "EARTH REFERENCE  /  SYNTHETIC FAMILY MESSAGE", fill="#e8e1d5")
        encoder.stdin.write(frame.tobytes())
    encoder.stdin.close()
    if encoder.wait():
        raise RuntimeError("Reference video encoding failed")

subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(video),
                "-map", "0:a:0", "-ac", "1", "-c:a", "libopus", "-b:a", "16k",
                str(dest / "message.ogg")], check=True)
