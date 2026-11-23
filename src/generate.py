#!/usr/bin/env python3
"""Generate a simple Polish 9:16 fact Short using free local tools."""

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import textwrap
import wave
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FACTS_FILE = ROOT / "data" / "facts.json"
OUTPUT_DIR = ROOT / "output"
WIDTH, HEIGHT = 1080, 1920


def require_program(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(
            f"Brakuje programu: {name}. Uruchom generator w workflow GitHub Actions "
            "albo zainstaluj wymagane narzędzia."
        )
    return path


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def wrap_pixels(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and draw.textbbox((0, 0), candidate, font=font)[2] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]


def draw_centered_block(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    font: ImageFont.ImageFont,
    max_width: int,
    fill: tuple[int, int, int],
    line_gap: int = 20,
) -> int:
    lines = wrap_pixels(draw, text, font, max_width)
    for line in lines:
        box = draw.textbbox((0, 0), line, font=font)
        line_height = box[3] - box[1]
        draw.text(((WIDTH - (box[2] - box[0])) / 2, y), line, font=font, fill=fill)
        y += line_height + line_gap
    return y


def make_poster(fact: dict, destination: Path) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT))
    pixels = image.load()

    # A simple dark blue-to-purple gradient, generated locally.
    top = (8, 18, 39)
    bottom = (37, 20, 58)
    for y in range(HEIGHT):
        ratio = y / (HEIGHT - 1)
        color = tuple(int(top[i] * (1 - ratio) + bottom[i] * ratio) for i in range(3))
        for x in range(WIDTH):
            pixels[x, y] = color

    draw = ImageDraw.Draw(image, "RGBA")

    # Subtle decorative circles and lines.
    draw.ellipse((760, 100, 1210, 550), outline=(104, 126, 255, 65), width=5)
    draw.ellipse((-190, 1280, 250, 1720), outline=(255, 190, 90, 45), width=5)
    for x in range(80, WIDTH, 100):
        draw.line((x, 250, x + 110, 170), fill=(170, 180, 255, 18), width=2)

    white = (248, 249, 255, 255)
    muted = (187, 197, 220, 255)
    accent = (255, 198, 92, 255)

    brand_font = load_font(36, bold=True)
    tag_font = load_font(27, bold=True)
    title_font = load_font(77, bold=True)
    section_font = load_font(29, bold=True)
    body_font = load_font(52, bold=False)
    footer_font = load_font(25, bold=True)

    # Brand and number label.
    draw.rounded_rectangle((70, 78, 430, 150), radius=34, fill=(255, 255, 255, 22), outline=(255, 255, 255, 55), width=2)
    draw.text((105, 94), "FAKTORYIA", font=brand_font, fill=white)
    draw.rounded_rectangle((690, 88, 1010, 148), radius=28, fill=(255, 198, 92, 28), outline=(255, 198, 92, 95), width=2)
    label = f"FAKT NR {int(fact['id']):02d}"
    label_box = draw.textbbox((0, 0), label, font=tag_font)
    draw.text((850 - (label_box[2] - label_box[0]) / 2, 103), label, font=tag_font, fill=accent)

    # Headline.
    draw.text((80, 330), "CZY WIESZ, ŻE...", font=section_font, fill=accent)
    title_end = draw_centered_block(
        draw, str(fact["title"]), 430, title_font, 900, white, line_gap=24
    )

    # Main fact card.
    card_top = max(820, title_end + 70)
    card_bottom = 1500
    draw.rounded_rectangle(
        (58, card_top, 1022, card_bottom),
        radius=44,
        fill=(255, 255, 255, 20),
        outline=(255, 255, 255, 55),
        width=3,
    )
    draw.text((112, card_top + 58), "TAK WYGLĄDA FAKT", font=section_font, fill=accent)

    body_text = str(fact["script"])
    selected_font = body_font
    lines = wrap_pixels(draw, body_text, selected_font, 840)
    while len(lines) * 76 > (card_bottom - card_top - 210) and selected_font.size > 38:
        selected_font = load_font(selected_font.size - 2, bold=False)
        lines = wrap_pixels(draw, body_text, selected_font, 840)

    y = card_top + 145
    for line in lines:
        box = draw.textbbox((0, 0), line, font=selected_font)
        line_height = box[3] - box[1]
        draw.text((112, y), line, font=selected_font, fill=white)
        y += line_height + 25

    draw.text((80, 1610), "JEDNA CIEKAWOSTKA. ZERO ZGADYWANIA.", font=footer_font, fill=muted)
    draw.text((80, 1680), "ŹRÓDŁO I LINK ZNAJDZIESZ W OPISIE FILMU", font=footer_font, fill=accent)
    draw.rounded_rectangle((80, 1795, 1000, 1805), radius=5, fill=(255, 198, 92, 190))
    image.save(destination, format="PNG", optimize=True)


def clean_sentence(text: str) -> str:
    return text.strip().rstrip(".!? ").strip()


def generate(fact: dict) -> Path:
    espeak = require_program("espeak-ng")
    ffmpeg = require_program("ffmpeg")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fact_id = int(fact["id"])
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base = f"faktoryia_{fact_id:03d}_{stamp}"
    video_path = OUTPUT_DIR / f"{base}.mp4"
    copy_path = OUTPUT_DIR / f"{base}_opis.txt"

    script = clean_sentence(str(fact["script"]))
    if not script:
        raise ValueError(f"Fakt {fact_id} nie ma tekstu do narracji.")
    narration = f"Czy wiesz, że {script[0].lower() + script[1:]}. Źródło znajdziesz w opisie."

    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        poster = temp / "poster.png"
        audio = temp / "narration.wav"
        make_poster(fact, poster)

        subprocess.run(
            [espeak, "-v", "pl", "-s", "146", "-p", "48", "-a", "170", "-w", str(audio), narration],
            check=True,
            capture_output=True,
            text=True,
        )

        with wave.open(str(audio), "rb") as wav_file:
            duration = wav_file.getnframes() / float(wav_file.getframerate())
        if duration <= 0:
            raise RuntimeError("Lektor nie wygenerował poprawnego pliku audio.")

        # Slow zoom makes the static poster feel less motionless.
        video_filter = (
            "zoompan=z='min(zoom+0.00035,1.06)':"
            "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            "d=1:s=1080x1920:fps=30,format=yuv420p"
        )
        subprocess.run(
            [
                ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                "-loop", "1", "-i", str(poster), "-i", str(audio),
                "-vf", video_filter, "-t", f"{duration:.3f}",
                "-r", "30", "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "23", "-c:a", "aac", "-b:a", "160k",
                "-shortest", "-movflags", "+faststart",
                "-metadata", f"title={fact['title']}",
                str(video_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    source = str(fact["source"])
    domain = urlparse(source).netloc or source
    copy_path.write_text(
        f"{fact['title']}\n\n{script}.\n\nŹródło: {source}\n",
        encoding="utf-8",
    )
    print(f"Gotowe wideo: {video_path}")
    print(f"Opis i źródło: {copy_path}")
    print(f"Czas narracji: {duration:.1f} s | Źródło: {domain}")
    return video_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generator polskich filmów Faktoryia Shorts.")
    parser.add_argument("--fact-id", type=int, help="ID konkretnej ciekawostki. Bez tej opcji wybór jest losowy.")
    args = parser.parse_args()

    if not FACTS_FILE.exists():
        print(f"Nie znaleziono pliku z faktami: {FACTS_FILE}", file=sys.stderr)
        return 1

    try:
        facts = json.loads(FACTS_FILE.read_text(encoding="utf-8"))
        if not isinstance(facts, list) or not facts:
            raise ValueError("data/facts.json musi zawierać niepustą listę faktów.")
        for item in facts:
            for key in ("id", "title", "script", "source"):
                if key not in item or not str(item[key]).strip():
                    raise ValueError(f"Jeden z faktów nie zawiera poprawnego pola: {key}")
        if args.fact_id is not None:
            matches = [item for item in facts if int(item["id"]) == args.fact_id]
            if not matches:
                raise ValueError(f"Nie ma faktu o ID {args.fact_id}.")
            fact = matches[0]
        elif os.environ.get("GITHUB_EVENT_NAME") == "schedule":
            # One deterministic fact per day: cycle through the list without repeats.
            day_number = datetime.now(timezone.utc).date().toordinal()
            fact = facts[day_number % len(facts)]
        else:
            fact = random.choice(facts)

        generate(fact)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, subprocess.CalledProcessError, RuntimeError) as exc:
        print(f"BŁĄD GENERATORA: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
