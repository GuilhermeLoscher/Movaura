from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CRITICAL_PLACEHOLDERS = ("PENDING", "master-latest")
REQUIRED_FILES = (
    "THIRD_PARTY_NOTICES.txt",
    "docs/FINAL_LICENSE_AUDIT.md",
    "docs/QT_MODULE_LICENSE_MATRIX.md",
    "docs/LGPL_MSIX_TECHNICAL_ASSESSMENT.md",
    "docs/FFMPEG_EXTERNAL_LIBRARY_MATRIX.md",
    "docs/FFMPEG_BUILD_LOCK.md",
    "docs/CODEC_PATENT_RISK_REGISTER.md",
    "docs/PYTHON_DEPENDENCY_LICENSE_MATRIX.md",
    "docs/THIRD_PARTY_COMPONENTS_LOCK.md",
    "docs/THIRD_PARTY_NOTICES.md",
    "docs/EULA_DRAFT_PT_BR.md",
    "docs/EULA_DRAFT_EN_US.md",
    "docs/PRIVACY_POLICY.md",
    "docs/LICENSE_COMPLIANCE_TEST_REPORT.md",
    "docs/LEGAL_REVIEW_HANDOFF.md",
    "third_party/ffmpeg/LOCK.json",
    "release/compliance/ffmpeg/ffmpeg-audit.json",
    "release/compliance/qt/qt-module-license-matrix.json",
    "release/compliance/python/python-dependency-license-matrix.json",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Movaura third-party license payload.")
    parser.add_argument("--report-only", action="store_true", help="Write findings and return success even when blockers exist.")
    args = parser.parse_args()

    findings: list[dict[str, str]] = []
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        if not path.is_file():
            findings.append({"severity": "critical", "path": relative, "message": "required compliance file is missing"})

    lock_path = ROOT / "third_party" / "ffmpeg" / "LOCK.json"
    if lock_path.is_file():
        lock = json.loads(read(lock_path))
        for field in ("artifact_name", "artifact_url", "archive_sha256", "ffmpeg_commit", "provider_commit", "source_url", "source_archive_sha256"):
            value = str(lock.get(field, ""))
            if not value or value.upper().startswith("PENDING"):
                findings.append({"severity": "critical", "path": str(lock_path.relative_to(ROOT)), "message": f"FFmpeg lock field is incomplete: {field}"})
        if "master-latest" in json.dumps(lock, ensure_ascii=False).lower():
            findings.append({"severity": "critical", "path": str(lock_path.relative_to(ROOT)), "message": "FFmpeg lock still references master-latest"})
        if not lock.get("files"):
            findings.append({"severity": "critical", "path": str(lock_path.relative_to(ROOT)), "message": "FFmpeg lock has no binary file hashes"})

    for relative in (
        "licenses/ffmpeg/NOTICE.txt",
        "licenses/ffmpeg/SOURCE.txt",
        "docs/FFMPEG_BUILD_LOCK.md",
        "docs/FINAL_LICENSE_AUDIT.md",
        "docs/FFMPEG_EXTERNAL_LIBRARY_MATRIX.md",
    ):
        path = ROOT / relative
        if path.is_file() and "master-latest" in read(path).lower():
            findings.append({"severity": "high", "path": relative, "message": "master-latest reference remains"})

    for relative in (
        "third_party/ffmpeg/LOCK.json",
        "docs/FFMPEG_BUILD_LOCK.md",
        "docs/FFMPEG_EXTERNAL_LIBRARY_MATRIX.md",
        "docs/QT_MODULE_LICENSE_MATRIX.md",
        "THIRD_PARTY_NOTICES.txt",
    ):
        path = ROOT / relative
        if path.is_file():
            content = read(path)
            if "PENDING" in content:
                findings.append({"severity": "critical", "path": relative, "message": "PENDING placeholder remains in release compliance payload"})

    qt_matrix = ROOT / "release" / "compliance" / "qt" / "qt-module-license-matrix.json"
    if qt_matrix.is_file():
        try:
            for item in json.loads(read(qt_matrix)):
                haystack = json.dumps(item, ensure_ascii=False).lower()
                if "virtualkeyboard" in haystack:
                    findings.append({"severity": "critical", "path": str(qt_matrix.relative_to(ROOT)), "message": "Qt Virtual Keyboard is present in the distributed artifact"})
                if "pending" in haystack:
                    findings.append({"severity": "critical", "path": str(qt_matrix.relative_to(ROOT)), "message": "Qt matrix contains pending classification"})
                    break
        except json.JSONDecodeError as exc:
            findings.append({"severity": "critical", "path": str(qt_matrix.relative_to(ROOT)), "message": f"invalid Qt matrix JSON: {exc}"})

    ffmpeg_matrix = ROOT / "docs" / "FFMPEG_EXTERNAL_LIBRARY_MATRIX.md"
    if ffmpeg_matrix.is_file() and "BLOCKER UNTIL CLASSIFIED" in read(ffmpeg_matrix):
        findings.append({"severity": "critical", "path": str(ffmpeg_matrix.relative_to(ROOT)), "message": "FFmpeg external library matrix still contains unclassified blockers"})

    for relative in (
        "licenses/qt/LGPL-3.0.txt",
        "licenses/qt/GPL-3.0.txt",
        "licenses/pyside6/LGPL-3.0.txt",
        "licenses/pyside6/GPL-3.0.txt",
        "licenses/shiboken6/LGPL-3.0.txt",
        "licenses/shiboken6/GPL-3.0.txt",
        "licenses/ffmpeg/LICENSE.txt",
    ):
        path = ROOT / relative
        if not path.is_file() or path.stat().st_size < 1000:
            findings.append({"severity": "critical", "path": relative, "message": "required license text is missing or too small"})

    beta_name = "Movaura Beta"
    for relative in ("release/compliance/inventories/project-file-manifest.json", "release/compliance/msix/msix-file-manifest.json"):
        path = ROOT / relative
        if path.is_file() and beta_name.lower() in read(path).lower():
            findings.append({"severity": "critical", "path": relative, "message": "Movaura Beta content appears in a release inventory"})

    report = {
        "status": "failed" if any(item["severity"] in {"critical", "high"} for item in findings) else "ok",
        "findings": findings,
        "note": "An ok status means the technical compliance payload is internally consistent. Professional legal review is still required for LGPL/MSIX, FFmpeg external libraries, codec patents, territories, EULA, privacy, and final publication decisions.",
    }
    output = ROOT / "release" / "compliance" / "reports" / "license-payload-validation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"license_payload={report['status']}")
    for finding in findings:
        print(f"{finding['severity']}: {finding['path']}: {finding['message']}")
    return 0 if args.report_only or report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
