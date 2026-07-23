from __future__ import annotations

import sys
import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import TextIO

from core.runtime_paths import data_root
from core.crash_report import write_crash_report


MAX_LOG_BYTES = 1_000_000
LOG_BACKUPS = 3


def log_path() -> Path:
    return data_root() / "logs" / "movaura.log"


class TeeStream:
    def __init__(self, terminal: TextIO | None, log_file: TextIO) -> None:
        self.terminal = terminal
        self.log_file = log_file
        self.lock = Lock()

    def write(self, text: str) -> int:
        with self.lock:
            if self.terminal:
                self.terminal.write(text)
            self.log_file.write(text)
            self.log_file.flush()
        return len(text)

    def flush(self) -> None:
        with self.lock:
            if self.terminal:
                self.terminal.flush()
            self.log_file.flush()

    def isatty(self) -> bool:
        return bool(self.terminal and self.terminal.isatty())

    @property
    def encoding(self) -> str:
        return (self.terminal and self.terminal.encoding) or "utf-8"


def configure_logging() -> Path:
    path = log_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        path = Path(tempfile.gettempdir()) / "Movaura" / "movaura.log"
        path.parent.mkdir(parents=True, exist_ok=True)
    try:
        _rotate_logs(path)
    except OSError:
        pass
    try:
        log_file = path.open("a", encoding="utf-8")
    except OSError:
        path = Path(tempfile.gettempdir()) / "Movaura" / "movaura.log"
        path.parent.mkdir(parents=True, exist_ok=True)
        log_file = path.open("a", encoding="utf-8")
    sys.stdout = TeeStream(sys.stdout, log_file)
    sys.stderr = TeeStream(sys.stderr, log_file)
    sys.excepthook = _exception_hook
    print()
    print(f"===== Movaura iniciado em {datetime.now().isoformat(timespec='seconds')} =====")
    return path


def _exception_hook(exc_type, exc_value, exc_traceback) -> None:
    try:
        path = write_crash_report(exc_type, exc_value, exc_traceback)
        print(f"Movaura: falha nao tratada. Relatorio salvo em: {path}", file=sys.stderr)
    except OSError:
        print("Movaura: falha nao tratada.", file=sys.stderr)
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)


def _rotate_logs(path: Path) -> None:
    if not path.exists() or path.stat().st_size < MAX_LOG_BYTES:
        return
    oldest = path.with_suffix(f"{path.suffix}.{LOG_BACKUPS}")
    if oldest.exists():
        oldest.unlink()
    for index in range(LOG_BACKUPS - 1, 0, -1):
        source = path.with_suffix(f"{path.suffix}.{index}")
        if source.exists():
            source.replace(path.with_suffix(f"{path.suffix}.{index + 1}"))
    path.replace(path.with_suffix(f"{path.suffix}.1"))
