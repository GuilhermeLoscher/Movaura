from __future__ import annotations

import argparse
import sys
from pathlib import Path

BLOCKED_TEXT = (
    "PyQt6",
    "PyQt6-Qt6",
    "PyQt6-sip",
    "pyqtSignal",
    "pyqtSlot",
    "pyqtProperty",
)
BLOCKED_PATH_PARTS = (
    "PyQt6",
    "PyQt6-Qt6",
    "PyQt6_sip",
    "PyQt6-sip",
)
TEXT_SUFFIXES = {
    ".py",
    ".txt",
    ".md",
    ".json",
    ".yml",
    ".yaml",
    ".ps1",
    ".cmd",
    ".spec",
    ".xml",
}
IGNORED_DIRS = {
    ".git",
    "__pycache__",
    "build",
    "dist",
    "release",
    "tools",
}
SOURCE_ALLOWLIST = {
    Path("docs/PYSIDE6_MIGRATION_INVENTORY.md"),
    Path("scripts/check_no_pyqt_artifacts.py"),
}


def iter_files(paths: list[Path], source_mode: bool) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if not path.exists():
            continue
        if path.is_file():
            files.append(path)
            continue
        for current in path.rglob("*"):
            if not current.is_file():
                continue
            if source_mode and any(part in IGNORED_DIRS for part in current.parts):
                continue
            files.append(current)
    return files


def scan(paths: list[Path], source_mode: bool) -> list[str]:
    root = Path.cwd().resolve()
    findings: list[str] = []
    for path in iter_files(paths, source_mode):
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(root)
        except ValueError:
            relative = resolved
        if source_mode and relative in SOURCE_ALLOWLIST:
            continue
        path_text = str(relative).replace("\\", "/")
        for blocked in BLOCKED_PATH_PARTS:
            if blocked.lower() in path_text.lower():
                findings.append(f"path:{path_text}:{blocked}")
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                text = path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                continue
        for line_no, line in enumerate(text.splitlines(), 1):
            for blocked in BLOCKED_TEXT:
                if blocked in line:
                    findings.append(f"text:{path_text}:{line_no}:{blocked}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail if Movaura source/build contains PyQt6 leftovers.")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--artifact", action="store_true", help="Scan a build artifact/layout instead of source tree.")
    args = parser.parse_args()
    findings = scan(args.paths, source_mode=not args.artifact)
    if findings:
        print("pyqt_artifact_check=failed")
        for item in findings[:200]:
            print(item)
        if len(findings) > 200:
            print(f"... {len(findings) - 200} more finding(s)")
        return 1
    print("pyqt_artifact_check=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())