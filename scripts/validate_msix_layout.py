from __future__ import annotations

import argparse
import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path


FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".pfx", ".pem", ".key", ".env", ".log", ".tmp"}
FORBIDDEN_NAMES = {".git", "__pycache__"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate generated Movaura MSIX layout.")
    parser.add_argument("layout", type=Path)
    parser.add_argument("--expected-package-name", default="")
    parser.add_argument("--expected-publisher", default="")
    parser.add_argument("--reports", type=Path, default=Path("release/reports"))
    args = parser.parse_args()

    layout = args.layout.resolve()
    reports = args.reports
    reports.mkdir(parents=True, exist_ok=True)
    findings: list[dict[str, str]] = []
    rows: list[dict[str, object]] = []
    manifest_path = layout / "AppxManifest.xml"

    if not layout.exists():
        findings.append({"severity": "critical", "message": f"layout not found: {layout}"})
    if not manifest_path.exists():
        findings.append({"severity": "critical", "message": "AppxManifest.xml missing"})

    identity: dict[str, str] = {}
    if manifest_path.exists():
        root = ET.parse(manifest_path).getroot()
        ns = {"m": "http://schemas.microsoft.com/appx/manifest/foundation/windows10"}
        element = root.find("m:Identity", ns)
        if element is not None:
            identity = dict(element.attrib)
        if args.expected_package_name and identity.get("Name") != args.expected_package_name:
            findings.append({"severity": "high", "message": "PackageName differs from expected identity"})
        if args.expected_publisher and identity.get("Publisher") != args.expected_publisher:
            findings.append({"severity": "high", "message": "Publisher differs from expected identity"})

    for path in sorted(layout.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(layout).as_posix()
        rows.append({"path": relative, "size": path.stat().st_size, "sha256": sha256(path)})
        parts = {part.lower() for part in path.parts}
        if any(name in parts for name in FORBIDDEN_NAMES):
            findings.append({"severity": "high", "message": f"forbidden directory in package: {relative}"})
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            findings.append({"severity": "high", "message": f"forbidden file suffix in package: {relative}"})
        if "Movaura Beta".lower() in str(path).lower():
            findings.append({"severity": "critical", "message": f"Movaura Beta artifact in package: {relative}"})

    with (reports / "msix-file-inventory.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "size", "sha256"])
        writer.writeheader()
        writer.writerows(rows)
    (reports / "msix-file-inventory.json").write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    (reports / "msix-sha256.txt").write_text(
        "".join(f"{row['sha256']}  {row['path']}\n" for row in rows),
        encoding="utf-8",
    )
    status = "failed" if any(item["severity"] in {"critical", "high"} for item in findings) else "ok"
    report = {
        "status": status,
        "layout": str(layout),
        "identity": identity,
        "file_count": len(rows),
        "total_size": sum(int(row["size"]) for row in rows),
        "findings": findings,
    }
    (reports / "msix-validation.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "Movaura MSIX layout validation",
        f"status: {status}",
        f"layout: {layout}",
        f"identity: {identity}",
        f"file_count: {len(rows)}",
        "",
        "Findings:",
    ]
    for item in findings:
        lines.append(f"- {item['severity']}: {item['message']}")
    (reports / "msix-validation.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"msix_validation={status}")
    return 1 if status == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
