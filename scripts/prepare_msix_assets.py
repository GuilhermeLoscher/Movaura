from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image


def save_square(source: Path, target: Path, size: int) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    image = Image.open(source).convert("RGBA")
    image.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    left = (size - image.width) // 2
    top = (size - image.height) // 2
    canvas.alpha_composite(image, (left, top))
    canvas.save(target)


def main() -> int:
    if len(sys.argv) != 3:
        print("uso: prepare_msix_assets.py <logo-origem> <pasta-assets>", file=sys.stderr)
        return 2
    source = Path(sys.argv[1])
    target_dir = Path(sys.argv[2])
    if not source.is_file():
        print(f"logo nao encontrado: {source}", file=sys.stderr)
        return 2
    save_square(source, target_dir / "StoreLogo.png", 50)
    save_square(source, target_dir / "Square44x44Logo.png", 44)
    save_square(source, target_dir / "Square150x150Logo.png", 150)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
