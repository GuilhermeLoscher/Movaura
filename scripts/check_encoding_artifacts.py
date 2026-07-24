from __future__ import annotations

import argparse
from pathlib import Path


MOJIBAKE_MARKERS = (
    "Ã¡",
    "Ãà",
    "Ã¢",
    "Ã£",
    "Ã©",
    "Ãª",
    "Ã­",
    "Ã³",
    "Ã´",
    "Ãµ",
    "Ãº",
    "Ã§",
    "Ã‡",
    "Âº",
    "Âª",
    "Â¿",
    "Â¡",
    "�",
)
TEXT_SUFFIXES = {".py", ".md", ".txt", ".json", ".yml", ".yaml", ".ps1", ".cmd", ".xml"}
IGNORED_DIRS = {".git", "build", "dist", "release", "tools", "__pycache__"}
SOURCE_ALLOWLIST = {Path("scripts/check_encoding_artifacts.py")}


def scan(paths: list[Path]) -> list[str]:
    findings: list[str] = []
    root = Path.cwd().resolve()
    for base in paths:
        candidates = [base] if base.is_file() else base.rglob("*")
        for path in candidates:
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if any(part in IGNORED_DIRS for part in path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                findings.append(f"encoding:{path}:{exc}")
                continue
            try:
                relative = path.resolve().relative_to(root)
            except ValueError:
                relative = path
            if relative in SOURCE_ALLOWLIST:
                continue
            for line_no, line in enumerate(text.splitlines(), 1):
                for marker in MOJIBAKE_MARKERS:
                    if marker in line:
                        findings.append(f"mojibake:{relative}:{line_no}:{marker}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect common UTF-8 mojibake markers in text files.")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--report", type=Path, default=Path("release/reports/encoding-audit.txt"))
    args = parser.parse_args()
    findings = scan(args.paths)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    if findings:
        args.report.write_text("encoding_audit=failed\n" + "\n".join(findings) + "\n", encoding="utf-8")
        print("encoding_audit=failed")
        for item in findings[:200]:
            print(item.encode("utf-8", errors="backslashreplace").decode("utf-8"))
        return 1
    args.report.write_text("encoding_audit=ok\n", encoding="utf-8")
    print("encoding_audit=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
