from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from core.wallpaper_library import WallpaperLibrary
from ui.library_dialog import LibraryDialog


def make_image(path: Path, color: int) -> None:
    image = QImage(96, 54, QImage.Format.Format_RGB32)
    image.fill(color)
    if not image.save(str(path)):
        raise RuntimeError(f"Could not create benchmark image: {path}")


def elapsed_ms(action) -> float:
    start = time.perf_counter()
    action()
    return (time.perf_counter() - start) * 1000


def main() -> None:
    app = QApplication.instance() or QApplication([])
    count = int(os.environ.get("MOVAURA_BENCHMARK_ITEMS", "500"))
    with TemporaryDirectory() as temp:
        root = Path(temp)
        source = root / "source"
        source.mkdir()
        for index in range(count):
            category = "anime" if index % 2 == 0 else "natureza"
            make_image(source / f"{category}-wallpaper-{index:04d}.png", 0x003355 + index)

        library = WallpaperLibrary()
        library.included_root = root / "included"
        library.personal_root = root / "personal"
        library.personal_root.mkdir(parents=True, exist_ok=True)
        library.metadata_path = root / "library.json"
        library._metadata = {"favorites": [], "recent": [], "details": {}, "ui": {}}

        import_ms = elapsed_ms(lambda: library.import_folder(source))
        open_ms = elapsed_ms(lambda: LibraryDialog(library).close())
        dialog = LibraryDialog(library)
        search_ms = elapsed_ms(lambda: (dialog.search_edit.setText("anime"), dialog.refresh()))
        filter_ms = elapsed_ms(lambda: (dialog.filter_combo.setCurrentText("Anime"), dialog.refresh()))
        app.processEvents()
        visible = dialog.list_widget.count()
        dialog.close()

    print("library_benchmark=ok")
    print(f"items={count}")
    print(f"import_ms={import_ms:.1f}")
    print(f"open_ms={open_ms:.1f}")
    print(f"search_ms={search_ms:.1f}")
    print(f"filter_ms={filter_ms:.1f}")
    print(f"visible_after_filter={visible}")


if __name__ == "__main__":
    main()
