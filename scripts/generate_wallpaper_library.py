from __future__ import annotations

import json
import math
import random
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter
from imageio_ffmpeg import write_frames


ROOT = Path(__file__).resolve().parent.parent
LIBRARY = ROOT / "wallpapers"
STATIC_DIR = LIBRARY / "static"
GIF_DIR = LIBRARY / "gifs"
VIDEO_DIR = LIBRARY / "videos"

THEMES = [
    ("neon-city", (7, 11, 28), (0, 220, 255), (255, 35, 130)),
    ("arcane-gate", (18, 6, 30), (180, 70, 255), (255, 185, 40)),
    ("crimson-arena", (25, 4, 9), (255, 40, 45), (255, 160, 45)),
    ("astral-drift", (4, 10, 30), (70, 130, 255), (230, 80, 255)),
    ("emerald-ruins", (2, 20, 18), (30, 255, 170), (170, 255, 70)),
    ("synth-sunset", (28, 6, 24), (255, 65, 150), (255, 190, 60)),
    ("frost-core", (5, 16, 30), (80, 220, 255), (190, 245, 255)),
    ("void-blades", (8, 5, 18), (145, 70, 255), (255, 45, 120)),
    ("solar-kingdom", (28, 15, 3), (255, 205, 50), (255, 90, 30)),
    ("storm-temple", (5, 12, 24), (90, 150, 255), (230, 245, 255)),
    ("pixel-dungeon", (12, 9, 22), (255, 75, 120), (100, 240, 210)),
    ("mecha-reactor", (8, 17, 22), (0, 245, 220), (255, 115, 20)),
    ("moon-shrine", (12, 8, 30), (160, 115, 255), (255, 170, 220)),
    ("toxic-lab", (5, 17, 10), (120, 255, 70), (255, 210, 40)),
    ("cyber-rain", (3, 12, 20), (20, 210, 255), (255, 40, 170)),
    ("dragon-ember", (26, 5, 3), (255, 75, 25), (255, 205, 70)),
    ("ocean-relic", (3, 15, 28), (30, 200, 255), (80, 255, 195)),
    ("shadow-castle", (10, 7, 19), (135, 80, 255), (245, 75, 115)),
    ("retro-grid", (18, 4, 25), (255, 45, 190), (65, 220, 255)),
    ("celestial-bloom", (12, 5, 25), (255, 105, 205), (105, 200, 255)),
]


def blend(first: tuple[int, int, int], second: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(int(a + (b - a) * amount) for a, b in zip(first, second))


def render(theme_index: int, width: int, height: int, phase: float = 0.0) -> Image.Image:
    name, background, primary, secondary = THEMES[theme_index]
    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image, "RGBA")
    rng = random.Random(9100 + theme_index)

    for y in range(height):
        amount = y / max(1, height - 1)
        color = blend(background, blend(primary, secondary, 0.5), amount * 0.28)
        draw.line((0, y, width, y), fill=(*color, 255))

    horizon = int(height * 0.62)
    pulse = 0.5 + 0.5 * math.sin(phase * math.tau)
    center_x = width // 2 + int(math.sin(phase * math.tau) * width * 0.035)
    center_y = int(height * (0.42 + 0.02 * math.cos(phase * math.tau)))

    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow, "RGBA")
    for radius in range(int(width * 0.32), 0, -max(2, width // 120)):
        alpha = int(2 + 22 * (1 - radius / (width * 0.32)))
        color = blend(primary, secondary, radius / (width * 0.32))
        glow_draw.ellipse(
            (center_x - radius, center_y - radius, center_x + radius, center_y + radius),
            outline=(*color, alpha),
            width=max(1, width // 320),
        )
    glow = glow.filter(ImageFilter.GaussianBlur(max(2, width // 120)))
    image = Image.alpha_composite(image.convert("RGBA"), glow)
    draw = ImageDraw.Draw(image, "RGBA")

    for index in range(110):
        x = int((rng.random() * width + phase * width * (0.15 + index % 5 * 0.02)) % width)
        y = int(rng.random() * horizon)
        radius = 1 + (index % 4 == 0)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*secondary, 100 + index % 120))

    for ring in range(6):
        radius = int(width * (0.055 + ring * 0.035) * (0.92 + pulse * 0.08))
        draw.ellipse(
            (center_x - radius, center_y - radius, center_x + radius, center_y + radius),
            outline=(*blend(primary, secondary, ring / 6), 110),
            width=max(2, width // 360),
        )

    grid_color = (*primary, 90)
    for offset in range(-8, 9):
        bottom_x = center_x + offset * width // 9
        draw.line((center_x, horizon, bottom_x, height), fill=grid_color, width=max(1, width // 640))
    for index in range(11):
        amount = index / 10
        y = int(horizon + (height - horizon) * amount * amount)
        draw.line((0, y, width, y), fill=grid_color, width=max(1, width // 720))

    for index in range(13):
        x = int((index + 0.5) * width / 13)
        tower_height = int(height * (0.08 + rng.random() * 0.22))
        shift = int(math.sin((phase + index / 13) * math.tau) * width * 0.008)
        draw.rectangle((x + shift, horizon - tower_height, x + width // 48 + shift, horizon), fill=(*background, 235))
        for row in range(3, tower_height, max(6, height // 40)):
            draw.rectangle((x + shift + 3, horizon - row, x + shift + width // 64, horizon - row + 2), fill=(*secondary, 145))

    for line_y in range(0, height, max(3, height // 180)):
        draw.line((0, line_y, width, line_y), fill=(255, 255, 255, 9))

    draw.text((width * 0.035, height * 0.9), f"MOVAURA // {name.upper()}", fill=(*secondary, 145))
    return image.convert("RGB")


def generate_static() -> list[str]:
    files = []
    for index in range(len(THEMES)):
        path = STATIC_DIR / f"{index + 1:02d}-{THEMES[index][0]}.jpg"
        render(index, 1920, 1080, index / len(THEMES)).save(path, quality=91, optimize=True)
        files.append(path.name)
    return files


def generate_gifs() -> list[str]:
    files = []
    for index in range(len(THEMES)):
        path = GIF_DIR / f"{index + 1:02d}-{THEMES[index][0]}.gif"
        frames = [render(index, 640, 360, frame / 24) for frame in range(24)]
        frames[0].save(
            path,
            save_all=True,
            append_images=frames[1:],
            duration=70,
            loop=0,
            optimize=False,
        )
        files.append(path.name)
    return files


def generate_videos() -> list[str]:
    files = []
    for index in range(len(THEMES)):
        path = VIDEO_DIR / f"{index + 1:02d}-{THEMES[index][0]}.mp4"
        writer = write_frames(
            str(path),
            (960, 544),
            fps=24,
            codec="libopenh264",
            pix_fmt_in="rgb24",
            pix_fmt_out="yuv420p",
            output_params=["-b:v", "2600k", "-maxrate", "3200k", "-bufsize", "6400k", "-movflags", "+faststart"],
        )
        writer.send(None)
        try:
            for frame in range(48):
                writer.send(render(index, 960, 544, frame / 48).tobytes())
        finally:
            writer.close()
        files.append(path.name)
    return files


def main() -> None:
    LIBRARY.mkdir(parents=True, exist_ok=True)
    for directory in (STATIC_DIR, GIF_DIR, VIDEO_DIR):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir()

    manifest = {
        "name": "Movaura Original Wallpaper Library",
        "license": "Original assets generated for redistribution with Movaura.",
        "static": generate_static(),
        "gifs": generate_gifs(),
        "videos": generate_videos(),
    }
    (LIBRARY / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (LIBRARY / "LEIA-ME.txt").write_text(
        "MOVAURA - BIBLIOTECA ORIGINAL\n"
        "================================\n\n"
        "Esta pasta contem 20 imagens, 20 GIFs animados e 20 videos MP4.\n"
        "Todos os arquivos foram gerados originalmente para acompanhar o Movaura.\n"
        "Eles podem ser redistribuidos junto com o instalador do programa.\n",
        encoding="utf-8",
    )
    print("wallpaper library generated: 20 static, 20 gifs, 20 videos")


if __name__ == "__main__":
    main()
