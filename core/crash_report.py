from __future__ import annotations

import traceback
from datetime import datetime
from pathlib import Path
from types import TracebackType

from core.runtime_paths import data_root
from core.version import APP_VERSION


def write_crash_report(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType | None,
) -> Path:
    directory = data_root() / "crashes"
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = directory / f"movaura-crash-{timestamp}.txt"
    body = [
        f"MOVAURA {APP_VERSION} - RELATORIO DE FALHA",
        f"Gerado em: {datetime.now().isoformat(timespec='seconds')}",
        "",
        *traceback.format_exception(exc_type, exc_value, exc_traceback),
    ]
    path.write_text("".join(body), encoding="utf-8")
    return path
