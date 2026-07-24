from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RELEASE_COMPLIANCE = PROJECT_ROOT / "release" / "compliance"
DOCS_AUDIT = PROJECT_ROOT / "docs" / "audit-evidence"
MOVAURA_BETA = PROJECT_ROOT.parent / "Movaura Beta"


@dataclass
class FileRecord:
    path: str
    name: str
    size: int
    sha256: str
    package: str = "UNKNOWN"
    version: str = "UNKNOWN"
    declared_license: str = "UNKNOWN"
    source: str = "local artifact"
    classification: str = "REVIEW REQUIRED"
    required_action: str = "Classify license and verify redistribution obligations."
    evidence: str = ""


def ensure_dirs() -> None:
    for path in (
        RELEASE_COMPLIANCE / "environment",
        RELEASE_COMPLIANCE / "inventories",
        RELEASE_COMPLIANCE / "licenses",
        RELEASE_COMPLIANCE / "qt",
        RELEASE_COMPLIANCE / "ffmpeg",
        RELEASE_COMPLIANCE / "python",
        RELEASE_COMPLIANCE / "pyinstaller",
        RELEASE_COMPLIANCE / "msix",
        RELEASE_COMPLIANCE / "reports",
        DOCS_AUDIT,
    ):
        path.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def run_command(argv: list[str], cwd: Path | None = None, timeout: int = 120) -> dict[str, object]:
    try:
        completed = subprocess.run(
            argv,
            cwd=str(cwd or PROJECT_ROOT),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except Exception as exc:
        return {"argv": argv, "error": f"{type(exc).__name__}: {exc}"}


def file_record(path: Path, *, package: str = "UNKNOWN", version: str = "UNKNOWN", license_name: str = "UNKNOWN",
                source: str = "local artifact", classification: str = "REVIEW REQUIRED",
                required_action: str = "Classify license and verify redistribution obligations.",
                evidence: str = "") -> FileRecord:
    return FileRecord(
        path=str(path.resolve()),
        name=path.name,
        size=path.stat().st_size,
        sha256=sha256_file(path),
        package=package,
        version=version,
        declared_license=license_name,
        source=source,
        classification=classification,
        required_action=required_action,
        evidence=evidence,
    )


def scan_files(root: Path, patterns: tuple[str, ...] = ("*",)) -> list[Path]:
    if not root.exists():
        return []
    files: list[Path] = []
    for pattern in patterns:
        files.extend(path for path in root.rglob(pattern) if path.is_file())
    return sorted(set(files), key=lambda item: str(item).lower())


def file_manifest(root: Path, *, hash_limit_bytes: int | None = None) -> list[dict[str, object]]:
    if not root.exists():
        return []
    rows: list[dict[str, object]] = []
    for path in sorted(root.rglob("*"), key=lambda item: str(item).lower()):
        if not path.is_file():
            continue
        stat = path.stat()
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size": stat.st_size,
                "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "sha256": sha256_file(path) if hash_limit_bytes is None or stat.st_size <= hash_limit_bytes else "",
            }
        )
    return rows


def reparse_manifest(root: Path) -> list[dict[str, object]]:
    if not root.exists():
        return []
    rows: list[dict[str, object]] = []
    for path in sorted(root.rglob("*"), key=lambda item: str(item).lower()):
        try:
            if path.is_symlink():
                rows.append(
                    {
                        "path": path.relative_to(root).as_posix(),
                        "kind": "symlink",
                        "target": os.readlink(path),
                    }
                )
        except OSError as exc:
            rows.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "kind": "inspection-error",
                    "target": str(exc),
                }
            )
    return rows


def environment_snapshot() -> dict[str, object]:
    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(PROJECT_ROOT),
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "windows_release": platform.release(),
        "cwd": os.getcwd(),
        "git": {
            "status": run_command(["git", "status", "--short", "--branch"]),
            "branch": run_command(["git", "branch", "--show-current"]),
            "head": run_command(["git", "rev-parse", "HEAD"]),
            "remote": run_command(["git", "remote", "-v"]),
            "log": run_command(["git", "log", "-10", "--oneline"]),
            "diff_check": run_command(["git", "diff", "--check"]),
            "fsck": run_command(["git", "fsck", "--no-reflogs"], timeout=240),
            "status_ignored": run_command(["git", "status", "--ignored", "--short"]),
        },
    }


def classify_qt_file(path: Path) -> dict[str, str]:
    name = path.name
    lower = name.lower()
    license_name = "LGPL-3.0-or-commercial (Qt/PySide distribution; verify module-specific notices)"
    gpl_only = "No evidence found in local package metadata; verify against official Qt module documentation."
    decision = "KEEP - collected by PyInstaller or runtime dependency; legal review required."
    if "virtualkeyboard" in lower:
        decision = "REVIEW - Qt Virtual Keyboard has module-specific licensing; verify commercial/GPL/LGPL availability before release."
        gpl_only = "PENDING - module-specific verification required."
    if lower.endswith(".dll") and lower.startswith("qt6"):
        module = name.removesuffix(".dll")
    else:
        module = path.parent.name
    return {
        "module": module,
        "license": license_name,
        "lgpl_available": "PENDING OFFICIAL VERIFICATION",
        "gpl_only": gpl_only,
        "decision": decision,
    }


def normalize_license_text(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")).strip() + "\n"
