#!/usr/bin/env python3
"""Faktoryia: two-minute Polish 'what if?' videos with animated scenes and Piper TTS."""

from __future__ import annotations
import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "facts.json"
OUTPUT_DIR = ROOT / "output"
VOICE_DIR = ROOT / "voices"
W, H = 540, 960
FPS = 12


def font(size: int, bold: bool = False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def wrap(draw, text, used_font, max_width):
    words, lines, current = text.split(), [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if current and draw.textbbox((0, 0), trial, font=used_font)[2] > max_width:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def draw_scene(scene: dict, index: int, total: int, out: Path):
    palettes = [
        ((5, 10, 28), (22, 65, 105), (40, 170, 205)),
        ((7, 18, 34), (16, 76, 115), (95, 205, 225)),
        ((9, 15, 32), (34, 59, 89), (180, 210, 220)),
        ((10, 17, 37), (35, 65, 112), (195, 220, 245)),
        ((8, 18, 31), (21, 64, 79), (120, 190, 180)),
        ((4, 8, 23), (30, 48, 86), (220, 235, 250)),
    ]
    top, mid, accent = palettes[index % len(palettes)]
    image = Image.new("RGB", (W, H), top)
    px = image.load()
    for y in range(H):
        f = y / H
        c = tuple(int(top[k] * (1-f) + mid[k] * f) for k in range(3))
        for x in range(W):
            px[x, y] = c
    d = ImageDraw.Draw(image, "RGBA")

    # Atmospheric glow and a large scene-specific illustration.
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((55, 245, 485, 675), fill=(*accent, 45))
    glow = glow.filter(ImageFilter.GaussianBlur(45))
    image = Image.alpha_composite(image.convert("RGBA"), glow)
    d = ImageDraw.Draw(image, "RGBA")

    if index in (0, 3, 5):
        # Planet Earth.
        d.ellipse((82, 260, 458, 636), fill=(18, 83, 130, 255), outline=(145, 220, 255, 220), width=5)
        if index == 0:
            d.polygon([(160,350),(205,315),(250,335),(270,390),(235,425),(190,415),(155,455),(125,415)], fill=(73,150,105,255))
            d.polygon([(300,420),(350,390),(395,425),(370,485),(330,520),(295,480)], fill=(75,155,110,255))
        else:
            d.polygon([(160,350),(205,315),(250,335),(270,390),(235,425),(190,415),(155,455),(125,415)], fill=(205,225,235,255))
            d.polygon([(300,420),(350,390),(395,425),(370,485),(330,520),(295,480)], fill=(215,232,240,255))
            for y in range(315, 585, 36):
                d.arc((105,y,435,y+80), 0, 180, fill=(245,250,255,100), width=3)
    elif index == 1:
        # Ocean surface and spreading ice.
        d.rectangle((0, 470, W, 690), fill=(10, 80, 125, 255))
        for y in (500, 550, 610):
            d.arc((-80,y-30,620,y+70), 0, 180, fill=(100,210,235,190), width=6)
        d.polygon([(20,470),(95,440),(160,466),(225,430),(300,466),(390,438),(520,465),(540,490),(0,490)], fill=(220,240,245,255))
        for x,y in ((130,520),(270,580),(400,530)):
            d.polygon([(x-38,y),(x,y-20),(x+35,y+3),(x+5,y+18)], fill=(225,245,250,220))
    elif index == 2:
        # Clouds, river, land and underground layers.
        for x,y,rx,ry in ((110,340,65,34),(180,325,55,42),(240,345,70,30),(360,320,72,42)):
            d.ellipse((x-rx,y-ry,x+rx,y+ry), fill=(225,240,248,220))
        d.polygon([(0,520),(130,480),(250,520),(390,480),(540,520),(540,720),(0,720)], fill=(64,125,100,255))
        d.line((245,510,220,570,280,625,250,710), fill=(85,205,225,255), width=18)
        d.rectangle((0,720,W,850), fill=(80,65,54,255))
        for y in (755,800):
            d.line((0,y,W,y), fill=(165,140,115,130), width=3)
    elif index == 4:
        # Life on land and in the sea, shown as simple silhouettes.
        d.rectangle((0,570,W,760), fill=(10,75,110,255))
        d.ellipse((115,450,195,530), fill=(245,205,130,255))
        d.polygon([(150,510),(120,580),(185,580)], fill=(245,205,130,255))
        d.ellipse((315,500,385,555), fill=(230,235,240,255))
        d.polygon([(315,525),(270,500),(280,550)], fill=(230,235,240,255))
        for x in (70,460):
            d.line((x,570,x-10,490), fill=(90,180,130,255), width=9)
            d.ellipse((x-45,465,x+15,520), fill=(90,180,130,220))

    # Brand, chapter number and bold on-screen chapter caption.
    d.rounded_rectangle((28, 34, 225, 78), radius=18, fill=(10,25,45,255), outline=(120,190,220,180), width=1)
    d.text((45, 46), "FAKTORYIA  |  CO, GDYBY?", font=font(14, True), fill=(255,220,160,255))
    d.text((30, 115), f"{index+1:02d} / {total:02d}", font=font(17, True), fill=(170,215,235,255))
    caption_font = font(31, True)
    lines = wrap(d, str(scene["caption"]), caption_font, 470)
    y = 720
    for line in lines[:3]:
        d.text((30,y), line, font=caption_font, fill=(255,255,255,255), stroke_width=2, stroke_fill=(0,0,0,150))
        y += 42
    d.rounded_rectangle((28, 900, 512, 908), radius=4, fill=(255,255,255,45))
    d.rounded_rectangle((28, 900, 28 + int(484*(index+1)/total), 908), radius=4, fill=(255,196,120,255))
    image.convert("RGB").save(out, quality=94)


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def generate(episode: dict):
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("Brakuje FFmpeg lub FFprobe.")
    model = VOICE_DIR / "pl_PL-darkman-medium.onnx"
    if not model.exists():
        raise RuntimeError("Brak modelu głosu Piper pl_PL-darkman-medium.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base = f"faktoryia_odcinek_{int(episode['id']):03d}_{stamp}"
    video = OUTPUT_DIR / f"{base}.mp4"
    description = OUTPUT_DIR / f"{base}_opis.txt"

    narration = str(episode["script"]).strip()
    if len(narration.split()) < 180:
        raise ValueError("Scenariusz jest za krótki. Odcinek powinien mieć co najmniej 180 słów.")
    with tempfile.TemporaryDirectory() as td:
        temp = Path(td)
        audio = temp / "narration.wav"
        run([sys.executable, "-m", "piper", "--data-dir", str(VOICE_DIR), "-m", "pl_PL-darkman-medium", "-f", str(audio), "--", narration])
        probe = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(audio)], check=True, capture_output=True, text=True)
        audio_seconds = float(probe.stdout.strip())
        if not 95 <= audio_seconds <= 155:
            raise ValueError(f"Lektor ma {audio_seconds:.1f} s. Odcinek powinien trwać około 2 minut (95–155 s).")

        scenes = episode.get("scenes", [])
        if len(scenes) < 5:
            raise ValueError("Odcinek wymaga co najmniej 5 scen.")
        segment_duration = audio_seconds / len(scenes)
        segment_files = []
        for i, scene in enumerate(scenes):
            still = temp / f"scene_{i:02d}.png"
            segment = temp / f"segment_{i:02d}.mp4"
            draw_scene(scene, i, len(scenes), still)
            zoom = "min(zoom+0.00035,1.08)" if i % 2 == 0 else "if(lte(zoom,1.0),1.08,max(zoom-0.00035,1.0))"
            vf = f"zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps={FPS},format=yuv420p"
            run([ffmpeg,"-y","-hide_banner","-loglevel","error","-loop","1","-i",str(still),"-t",f"{segment_duration:.3f}","-vf",vf,"-r",str(FPS),"-c:v","libx264","-preset","veryfast","-crf","23","-pix_fmt","yuv420p",str(segment)])
            segment_files.append(segment)

        concat_file = temp / "concat.txt"
        concat_file.write_text("".join(f"file '{p.as_posix()}'\n" for p in segment_files), encoding="utf-8")
        silent = temp / "silent.mp4"
        run([ffmpeg,"-y","-hide_banner","-loglevel","error","-f","concat","-safe","0","-i",str(concat_file),"-c","copy",str(silent)])
        run([ffmpeg,"-y","-hide_banner","-loglevel","error","-i",str(silent),"-i",str(audio),"-map","0:v:0","-map","1:a:0","-t",f"{audio_seconds:.3f}","-c:v","copy","-c:a","aac","-b:a","160k","-movflags","+faststart","-metadata",f"title={episode['title']}",str(video)])

    source_lines = "\n".join(f"- {url}" for url in episode["sources"])
    description.write_text(f"{episode['title']}\n\n{episode.get('description','')}\n\nŹRÓDŁA:\n{source_lines}\n\n#cogdyby #nauka #ciekawostki #shorts\n", encoding="utf-8")
    print(f"Gotowy film: {video} ({audio_seconds:.1f} s)")
    print(f"Opis: {description}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode-id", type=int)
    args = parser.parse_args()
    try:
        episodes = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        if not isinstance(episodes, list) or not episodes:
            raise ValueError("data/facts.json musi zawierać listę odcinków.")
        for ep in episodes:
            for key in ("id","title","script","sources","scenes"):
                if key not in ep:
                    raise ValueError(f"Brakuje pola {key} w odcinku.")
        if args.episode_id is not None:
            matches = [e for e in episodes if int(e["id"]) == args.episode_id]
            if not matches:
                raise ValueError(f"Nie znaleziono odcinka {args.episode_id}.")
            episode = matches[0]
        elif os.environ.get("GITHUB_EVENT_NAME") == "schedule":
            episode = episodes[datetime.now(timezone.utc).date().toordinal() % len(episodes)]
        else:
            episode = episodes[0]
        generate(episode)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, subprocess.CalledProcessError, RuntimeError) as exc:
        print(f"BŁĄD: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
