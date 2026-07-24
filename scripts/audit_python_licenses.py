from __future__ import annotations

import importlib.metadata as metadata
import sys
from pathlib import Path

from license_compliance_common import RELEASE_COMPLIANCE, ensure_dirs, sha256_file, write_csv, write_json


RUNTIME_PACKAGES = {
    "PySide6",
    "PySide6_Addons",
    "PySide6_Essentials",
    "shiboken6",
    "pywin32",
    "Pillow",
}

BUILD_PACKAGES = {
    "pyinstaller",
    "pyinstaller-hooks-contrib",
    "altgraph",
    "packaging",
    "pefile",
    "pywin32-ctypes",
    "setuptools",
}


def dist_files(dist: metadata.Distribution) -> list[Path]:
    root = Path(str(dist.locate_file("")))
    files: list[Path] = []
    for item in dist.files or []:
        path = root / Path(str(item))
        if path.exists() and path.is_file():
            files.append(path)
    return files


def license_files(files: list[Path]) -> list[Path]:
    wanted = ("license", "copying", "notice", "authors")
    return [path for path in files if any(part in path.name.lower() for part in wanted)]


def main() -> int:
    ensure_dirs()
    rows = []
    for name in sorted(RUNTIME_PACKAGES | BUILD_PACKAGES, key=str.lower):
        try:
            dist = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            rows.append(
                {
                    "name": name,
                    "version": "NOT INSTALLED",
                    "wheel": "",
                    "hash": "",
                    "source": "metadata unavailable",
                    "license": "UNKNOWN",
                    "official_license_file": "",
                    "standalone": "UNKNOWN",
                    "msix": "UNKNOWN",
                    "build_only": str(name in BUILD_PACKAGES),
                    "notices": "Package not installed in this environment.",
                    "risk": "BLOCKER if redistributed.",
                    "evidence": "",
                }
            )
            continue
        files = dist_files(dist)
        licenses = license_files(files)
        metadata_text = dist.read_text("METADATA") or ""
        license_value = dist.metadata.get("License") or ""
        classifiers = [value.removeprefix("License :: ").strip() for value in dist.metadata.get_all("Classifier", []) if value.startswith("License ::")]
        if not license_value and classifiers:
            license_value = "; ".join(classifiers)
        rows.append(
            {
                "name": dist.metadata.get("Name", name),
                "version": dist.version,
                "wheel": str(Path(str(dist.locate_file("")))),
                "hash": sha256_file(licenses[0]) if licenses else "",
                "source": dist.metadata.get("Home-page") or dist.metadata.get("Project-URL") or "package metadata",
                "license": license_value or "UNKNOWN",
                "official_license_file": "; ".join(str(path) for path in licenses),
                "standalone": "YES" if name in RUNTIME_PACKAGES else "NO/BUILD TOOL",
                "msix": "YES" if name in RUNTIME_PACKAGES else "NO/BUILD TOOL",
                "build_only": str(name in BUILD_PACKAGES),
                "notices": "Preserve official license text; do not replace with summary.",
                "risk": "REVIEW REQUIRED" if not license_value or not licenses else "LOW/MEDIUM - verify notice obligations.",
                "evidence": metadata_text[:5000],
            }
        )
    fields = [
        "name", "version", "wheel", "hash", "source", "license", "official_license_file",
        "standalone", "msix", "build_only", "notices", "risk", "evidence",
    ]
    write_json(RELEASE_COMPLIANCE / "python" / "python-dependency-license-matrix.json", rows)
    write_csv(RELEASE_COMPLIANCE / "python" / "python-dependency-license-matrix.csv", rows, fields)
    write_json(
        RELEASE_COMPLIANCE / "environment" / "python-environment.json",
        {"python": sys.version, "executable": sys.executable, "packages": rows},
    )
    print(f"python_license_rows={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
