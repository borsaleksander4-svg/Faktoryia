#!/usr/bin/env python3
"""Render a vertical Faktoryia Short with animated Venus and neural Polish TTS."""

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
FACTS_FILE = ROOT / "data" / "facts.json"
OUTPUT_DIR = ROOT / "output"
VOICE_DIR = ROOT / "voices"
WIDTH, HEIGHT = 540, 960
FPS = 15
FRAMES = 120


def require_program(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"Brakuje programu: {name}")
    return path


def load_font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        if current and draw.textbbox((0, 0), test, font=font)[2] > max_width:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    return lines or [""]


def make_venus_texture(size: int = 440) -> Image.Image:
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = base.load()
    center = (size - 1) / 2
    radius = size * 0.48
    for y in range(size):
        for x in range(size):
            dx, dy = (x - center) / radius, (y - center) / radius
            rr = dx * dx + dy * dy
            if rr <= 1:
                light = max(0.0, 1.0 - math.sqrt(rr))
                band = math.sin(y * 0.075 + math.sin(x * 0.025) * 2.4)
                fine = math.sin(y * 0.19 + x * 0.035) * 0.10
                shade = max(0.0, min(1.0, 0.56 + band * 0.13 + fine + light * 0.28))
                px[x, y] = (
                    int(105 + shade * 135),
                    int(45 + shade * 125),
                    int(18 + shade * 72),
                    255,
                )
    # Soft atmospheric rim.
    rim = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rim)
    rd.ellipse((3, 3, size - 4, size - 4), outline=(255, 205, 130, 190), width=7)
    rim = rim.filter(ImageFilter.GaussianBlur(7))
    base.alpha_composite(rim)
    return base


def make_frame(fact: dict, frame_no: int, venus_texture: Image.Image, stars: list[tuple[int, int, int]]) -> Image.Image:
    t = frame_no / FPS
    image = Image.new("RGB", (WIDTH, HEIGHT), (5, 8, 22))
    px = image.load()
    for y in range(HEIGHT):
        v = y / HEIGHT
        c = (int(7 + 9 * v), int(12 + 8 * v), int(30 + 24 * v))
        for x in range(WIDTH):
            px[x, y] = c

    draw = ImageDraw.Draw(image, "RGBA")
    # Stars twinkle gently.
    for x, y, phase in stars:
        alpha = int(90 + 80 * (0.5 + 0.5 * math.sin(t * 2.0 + phase)))
        draw.ellipse((x, y, x + 2, y + 2), fill=(220, 230, 255, alpha))

    # Slow orbital rings behind Venus.
    ring_box = (38, 260, 502, 720)
    draw.ellipse(ring_box, outline=(255, 183, 110, 55), width=2)
    draw.ellipse((65, 290, 475, 690), outline=(160, 175, 255, 35), width=1)

    # Rotate the cloud texture to create a visible animated planet.
    angle = -frame_no * 1.2
    planet = venus_texture.rotate(angle, resample=Image.Resampling.BICUBIC)
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((62, 270, 478, 686), fill=(255, 151, 70, 38))
    glow = glow.filter(ImageFilter.GaussianBlur(28))
    image = Image.alpha_composite(image.convert("RGBA"), glow)
    image.alpha_composite(planet, (50, 258))
    draw = ImageDraw.Draw(image, "RGBA")

    # Header.
    title_font = load_font(27, True)
    small_font = load_font(15, True)
    body_font = load_font(22, True)
    draw.rounded_rectangle((28, 38, 218, 76), radius=18, fill=(255, 255, 255, 22), outline=(255, 255, 255, 60), width=1)
    draw.text((44, 47), "FAKTORYIA", font=small_font, fill=(255, 214, 155, 255))
    draw.text((30, 118), "CZY WIESZ, ŻE…", font=small_font, fill=(255, 195, 120, 255))
    title_lines = wrap_text(draw, str(fact["title"]), title_font, 480)
    y = 148
    for line in title_lines[:3]:
        draw.text((30, y), line, font=title_font, fill=(250, 248, 244, 255), stroke_width=1, stroke_fill=(15, 12, 25, 220))
        y += 36

    # Bottom fact panel, with no source URL on screen.
    draw.rounded_rectangle((24, 738, 516, 910), radius=24, fill=(12, 18, 38, 220), outline=(255, 195, 120, 100), width=2)
    body = str(fact["script"])
    lines = wrap_text(draw, body, body_font, 440)
    y = 765
    for line in lines[:4]:
        draw.text((48, y), line, font=body_font, fill=(240, 243, 250, 255))
        y += 31
    draw.text((30, 925), "ŹRÓDŁO W OPISIE FILMU", font=small_font, fill=(255, 195, 120, 255))
    # Animated progress indicator.
    progress = (frame_no + 1) / FRAMES
    draw.rounded_rectangle((30, 950, 510, 955), radius=3, fill=(80, 87, 112, 180))
    draw.rounded_rectangle((30, 950, 30 + int(480 * progress), 955), radius=3, fill=(255, 190, 115, 255))
    return image.convert("RGB")


def generate(fact: dict) -> Path:
    require_program("ffmpeg")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fact_id = int(fact["id"])
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base = f"faktoryia_{fact_id:03d}_{stamp}"
    video_path = OUTPUT_DIR / f"{base}.mp4"
    description_path = OUTPUT_DIR / f"{base}_opis.txt"

    script = str(fact["script"]).strip()
    if not script:
        raise ValueError(f"Fakt {fact_id} nie ma tekstu do narracji.")
    narration = f"Czy wiesz, że {script}"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        audio = temp / "narration.wav"
        frames_dir = temp / "frames"
        frames_dir.mkdir()
        voice_model = VOICE_DIR / "pl_PL-darkman-medium.onnx"
        if not voice_model.exists():
            raise RuntimeError("Brak modelu głosu Piper: pl_PL-darkman-medium")

        subprocess.run(
            [sys.executable, "-m", "piper", "--data-dir", str(VOICE_DIR), "-m", "pl_PL-darkman-medium", "-f", str(audio), "--", narration],
            check=True,
            capture_output=True,
            text=True,
        )

        venus = make_venus_texture()
        rng = random.Random(42)
        stars = [(rng.randrange(WIDTH), rng.randrange(HEIGHT), rng.randrange(100)) for _ in range(70)]
        for index in range(FRAMES):
            frame = make_frame(fact, index, venus, stars)
            frame.save(frames_dir / f"frame_{index:04d}.png", optimize=True)

        ffmpeg = shutil.which("ffmpeg")
        subprocess.run(
            [
                ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                "-framerate", str(FPS), "-i", str(frames_dir / "frame_%04d.png"),
                "-i", str(audio), "-vf", "scale=1080:1920:flags=lanczos,format=yuv420p",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
                "-metadata", f"title={fact['title']}", str(video_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    source = str(fact["source"])
    topic_tag = "#kosmos" if "wenus" in (str(fact["title"]) + " " + source).lower() else "#zwierzeta"
    description_path.write_text(
        f"{fact['title']}\n\n{script}\n\nŹródło:\n{source}\n\n#ciekawostki {topic_tag} #nauka #shorts\n",
        encoding="utf-8",
    )
    print(f"Gotowe wideo: {video_path}")
    print(f"Opis filmu: {description_path}")
    return video_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generator polskich filmów Faktoryia Shorts.")
    parser.add_argument("--fact-id", type=int, help="ID konkretnej ciekawostki. Bez tej opcji wybór jest losowy.")
    args = parser.parse_args()
    try:
        facts = json.loads(FACTS_FILE.read_text(encoding="utf-8"))
        if not isinstance(facts, list) or not facts:
            raise ValueError("data/facts.json musi zawierać niepustą listę faktów.")
        for item in facts:
            for key in ("id", "title", "script", "source"):
                if key not in item or not str(item[key]).strip():
                    raise ValueError(f"Brak poprawnego pola: {key}")
        if args.fact_id is not None:
            matches = [item for item in facts if int(item["id"]) == args.fact_id]
            if not matches:
                raise ValueError(f"Nie ma faktu o ID {args.fact_id}.")
            fact = matches[0]
        elif os.environ.get("GITHUB_EVENT_NAME") == "schedule":
            day_number = datetime.now(timezone.utc).date().toordinal()
            fact = facts[day_number % len(facts)]
        elif os.environ.get("GITHUB_EVENT_NAME") == "push":
            # A repository update produces a predictable demo: the Venus fact matches the planet animation.
            fact = facts[0]
        else:
            fact = random.choice(facts)
        generate(fact)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, subprocess.CalledProcessError, RuntimeError) as exc:
        print(f"BŁĄD GENERATORA: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
