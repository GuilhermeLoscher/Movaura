from __future__ import annotations

import os
from pathlib import Path


def normalize_path(path: str | Path) -> str:
    """Return a stable absolute-ish path key for comparisons on Windows."""
    raw = Path(path).expanduser()
    try:
        resolved = raw.resolve(strict=False)
    except OSError:
        resolved = raw.absolute()
    return os.path.normcase(os.path.normpath(str(resolved)))


def is_inside_path(path: str | Path, root: str | Path) -> bool:
    candidate = normalize_path(path)
    base = normalize_path(root)
    return candidate == base or candidate.startswith(base + os.sep)
