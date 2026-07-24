from __future__ import annotations

from pathlib import Path

from license_compliance_common import (
    PROJECT_ROOT,
    RELEASE_COMPLIANCE,
    classify_qt_file,
    ensure_dirs,
    file_record,
    write_csv,
    write_json,
)


def main() -> int:
    ensure_dirs()
    standalone = PROJECT_ROOT / "dist" / "standalone" / "Movaura"
    roots = [
        standalone / "_internal" / "PySide6",
        standalone / "_internal" / "shiboken6",
    ]
    files: list[Path] = []
    for root in roots:
        if root.exists():
            files.extend(path for path in root.rglob("*") if path.is_file())
    records = []
    matrix = []
    for path in sorted(files, key=lambda item: str(item).lower()):
        if path.suffix.lower() not in {".dll", ".pyd", ".exe", ".json", ".qml", ".qm"} and "plugins" not in path.parts:
            continue
        info = classify_qt_file(path)
        package = "shiboken6" if "shiboken6" in [part.lower() for part in path.parts] else "PySide6/Qt"
        record = file_record(
            path,
            package=package,
            version="6.10.0",
            license_name=info["license"],
            source="PySide6 6.10.0 wheel / PyInstaller artifact",
            classification="LGPL REVIEW REQUIRED",
            required_action=info["decision"],
            evidence="Local standalone artifact inventory; module-specific legal status must be checked against official Qt documentation.",
        )
        records.append(record)
        matrix.append(
            {
                "file_module": info["module"],
                "version": "6.10.0",
                "origin": package,
                "official_license": info["license"],
                "lgpl_available": info["lgpl_available"],
                "gpl_only": info["gpl_only"],
                "used": "YES - present in standalone artifact",
                "evidence": record.sha256,
                "decision": info["decision"],
                "path": str(path.resolve()),
            }
        )
    fields = list(records[0].__dataclass_fields__) if records else [
        "path", "name", "size", "sha256", "package", "version", "declared_license",
        "source", "classification", "required_action", "evidence",
    ]
    write_json(RELEASE_COMPLIANCE / "qt" / "qt-module-inventory.json", [record.__dict__ for record in records])
    write_csv(RELEASE_COMPLIANCE / "qt" / "qt-module-inventory.csv", [record.__dict__ for record in records], fields)
    write_json(RELEASE_COMPLIANCE / "qt" / "qt-module-license-matrix.json", matrix)
    write_csv(
        RELEASE_COMPLIANCE / "qt" / "qt-module-license-matrix.csv",
        matrix,
        ["file_module", "version", "origin", "official_license", "lgpl_available", "gpl_only", "used", "evidence", "decision", "path"],
    )
    print(f"qt_records={len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
