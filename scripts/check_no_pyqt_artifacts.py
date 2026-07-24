from __future__ import annotations

import argparse
import importlib.metadata
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
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
BLOCKED_DISTRIBUTIONS = (
    "PyQt6",
    "PyQt6-Qt6",
    "PyQt6-sip",
    "sip",
)
EXPECTED_DISTRIBUTIONS = (
    "PySide6",
    "PySide6_Addons",
    "PySide6_Essentials",
    "shiboken6",
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
    Path("docs/PYSIDE6_MIGRATION_REPORT.md"),
    Path("scripts/check_no_pyqt_artifacts.py"),
}


@dataclass(frozen=True)
class Finding:
    kind: str
    path: str
    token: str
    line: int | None = None
    detail: str = ""


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


def scan(paths: list[Path], source_mode: bool) -> list[Finding]:
    root = Path.cwd().resolve()
    findings: list[Finding] = []
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
                findings.append(Finding("path", path_text, blocked))
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
                    findings.append(Finding("text", path_text, blocked, line_no))
    return findings


def scan_installed_distributions() -> tuple[list[dict[str, str]], list[Finding]]:
    present: list[dict[str, str]] = []
    findings: list[Finding] = []
    for name in sorted(set(BLOCKED_DISTRIBUTIONS + EXPECTED_DISTRIBUTIONS), key=str.lower):
        try:
            version = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            continue
        present.append({"name": name, "version": version})
        if name in BLOCKED_DISTRIBUTIONS:
            findings.append(Finding("distribution", name, name, detail=f"installed {version}"))
    return present, findings


def run_pip_show() -> dict[str, object]:
    command = [
        sys.executable,
        "-m",
        "pip",
        "show",
        "PyQt6",
        "PyQt6-Qt6",
        "PyQt6-sip",
        "sip",
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def write_reports(report_base: Path, payload: dict[str, object]) -> None:
    report_base.parent.mkdir(parents=True, exist_ok=True)
    report_base.with_suffix(".json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    lines = [
        "Movaura Qt binding audit",
        f"status: {payload['status']}",
        f"source_mode: {payload['source_mode']}",
        f"artifact_mode: {payload['artifact_mode']}",
        f"findings: {len(payload['findings'])}",
        "",
        "Installed distributions:",
    ]
    for item in payload["installed_distributions"]:
        lines.append(f"- {item['name']}=={item['version']}")
    lines.extend(["", "pip show blocked packages:"])
    pip_show = payload["pip_show"]
    lines.append(str(pip_show.get("stdout") or pip_show.get("stderr") or "no blocked packages reported"))
    lines.extend(["", "Findings:"])
    for item in payload["findings"]:
        location = item["path"]
        if item.get("line"):
            location += f":{item['line']}"
        detail = f" ({item['detail']})" if item.get("detail") else ""
        lines.append(f"- {item['kind']} {location}: {item['token']}{detail}")
    lines.extend(
        [
            "",
            "Limitations:",
            "- Text/path/package metadata scanner only.",
            "- Binary string absence is not a formal proof of dependency absence.",
        ]
    )
    report_base.with_suffix(".txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail if Movaura source/build contains PyQt6 leftovers.")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--artifact", action="store_true", help="Scan a build artifact/layout instead of source tree.")
    parser.add_argument("--report-base", type=Path, default=None, help="Write .json and .txt audit reports at this base path.")
    parser.add_argument("--skip-env", action="store_true", help="Skip installed distribution and pip checks.")
    args = parser.parse_args()
    findings = scan(args.paths, source_mode=not args.artifact)
    installed: list[dict[str, str]] = []
    pip_show: dict[str, object] = {"skipped": True}
    if not args.skip_env:
        installed, env_findings = scan_installed_distributions()
        findings.extend(env_findings)
        pip_show = run_pip_show()
    status = "failed" if findings else "ok"
    payload = {
        "status": status,
        "source_mode": not args.artifact,
        "artifact_mode": args.artifact,
        "paths": [str(path) for path in args.paths],
        "blocked_text": list(BLOCKED_TEXT),
        "blocked_path_parts": list(BLOCKED_PATH_PARTS),
        "installed_distributions": installed,
        "pip_show": pip_show,
        "findings": [asdict(item) for item in findings],
        "limitations": [
            "Text/path/package metadata scanner only.",
            "Binary string absence is not a formal proof of dependency absence.",
        ],
    }
    if args.report_base:
        write_reports(args.report_base, payload)
    if findings:
        print("pyqt_artifact_check=failed")
        for item in findings[:200]:
            location = item.path
            if item.line:
                location += f":{item.line}"
            detail = f" ({item.detail})" if item.detail else ""
            print(f"{item.kind}:{location}:{item.token}{detail}")
        if len(findings) > 200:
            print(f"... {len(findings) - 200} more finding(s)")
        return 1
    print("pyqt_artifact_check=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
