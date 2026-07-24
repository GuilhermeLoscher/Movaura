# License compliance test report

## environment

```json
{
  "created_at_utc": "2026-07-24T14:38:46.812869+00:00",
  "project_root": "C:\\NovaWall\\Movaura",
  "python": "3.12.13 (main, Mar  3 2026, 15:01:35) [MSC v.1944 64 bit (AMD64)]",
  "python_executable": "C:\\NovaWall\\.build-venv\\Scripts\\python.exe",
  "platform": "Windows-11-10.0.26200-SP0",
  "machine": "AMD64",
  "processor": "Intel64 Family 6 Model 140 Stepping 1, GenuineIntel",
  "windows_release": "11",
  "cwd": "C:\\NovaWall\\Movaura",
  "git": {
    "status": {
      "argv": [
        "git",
        "status",
        "--short",
        "--branch"
      ],
      "returncode": 0,
      "stdout": "## audit/license-compliance-final...origin/audit/license-compliance-final\n M THIRD_PARTY_NOTICES.txt\n M docs/CODEC_PATENT_RISK_REGISTER.md\n M docs/FFMPEG_BUILD_LOCK.md\n M docs/FFMPEG_EXTERNAL_LIBRARY_MATRIX.md\n M docs/FFMPEG_LGPL_REVIEW.md\n M docs/FINAL_LICENSE_AUDIT.md\n M docs/LEGAL_REVIEW_HANDOFF.md\n M docs/LGPL_MSIX_TECHNICAL_ASSESSMENT.md\n M docs/LICENSE_COMPLIANCE_TEST_REPORT.md\n M docs/QT_MODULE_LICENSE_MATRIX.md\n M docs/THIRD_PARTY_COMPONENTS_LOCK.md\n M docs/THIRD_PARTY_NOTICES.md\n M licenses/ffmpeg/BUILD_CONFIGURATION.txt\n M licenses/ffmpeg/NOTICE.txt\n M licenses/ffmpeg/SOURCE.txt\n M licenses/pillow/LICENSE\n M licenses/pyinstaller/COPYING.txt\n M release/compliance/environment/baseline.json\n M release/compliance/ffmpeg/ffmpeg-audit.json\n M release/compliance/ffmpeg/ffmpeg-audit.txt\n M release/compliance/inventories/project-file-manifest.json\n M release/compliance/inventories/sbom-spdx.json\n M release/compliance/inventories/standalone-file-manifest.json\n M release/compliance/msix/msix-file-manifest.json\n M release/compliance/python/python-dependency-license-matrix.csv\n M release/compliance/qt/qt-module-inventory.csv\n M release/compliance/qt/qt-module-inventory.json\n M release/compliance/qt/qt-module-license-matrix.csv\n M release/compliance/qt/qt-module-license-matrix.json\n M release/compliance/reports/license-compliance-prep-results.json\n M release/compliance/reports/license-payload-validation.json\n M scripts/audit_ffmpeg_compliance.py\n M scripts/build_standalone.ps1\n M scripts/license_compliance_common.py\n M scripts/prepare_license_compliance_docs.py\n M scripts/validate_license_payload.py\n M third_party/ffmpeg/LOCK.json\n M third_party_sources/ffmpeg/BUILD_CONFIGURATION.txt\n M third_party_sources/ffmpeg/BUILD_PROVENANCE.json\n M third_party_sources/ffmpeg/CHECKSUMS.txt\n M third_party_sources/ffmpeg/SOURCE_SHA256.txt\n M third_party_sources/ffmpeg/SOURCE_URL.txt\n?? licenses/ffmpeg/LICENSE.txt\n?? licenses/pyside6/GPL-2.0.txt\n?? licenses/pyside6/GPL-3.0.txt\n?? licenses/pyside6/LGPL-2.1.txt\n?? licenses/pyside6/LGPL-3.0.txt\n?? licenses/qt/GPL-2.0.txt\n?? licenses/qt/GPL-3.0.txt\n?? licenses/qt/LGPL-2.1.txt\n?? licenses/qt/LGPL-3.0.txt\n?? licenses/shiboken6/GPL-2.0.txt\n?? licenses/shiboken6/GPL-3.0.txt\n?? licenses/shiboken6/LGPL-2.1.txt\n?? licenses/shiboken6/LGPL-3.0.txt\n?? scripts/ensure_ffmpeg_binary.py\n?? scripts/finalize_phase2_license_blockers.py\n",
      "stderr": ""
    },
    "branch": {
      "argv": [
        "git",
        "branch",
        "--show-current"
      ],
      "returncode": 0,
      "stdout": "audit/license-compliance-final\n",
      "stderr": ""
    },
    "head": {
      "argv": [
        "git",
        "rev-parse",
        "HEAD"
      ],
      "returncode": 0,
      "stdout": "ad18ee50a9672ecf93a8d2a04372f88c2199a8cc\n",
      "stderr": ""
    },
    "remote": {
      "argv": [
        "git",
        "remote",
        "-v"
      ],
      "returncode": 0,
      "stdout": "origin\thttps://github.com/GuilhermeLoscher/Movaura.git (fetch)\norigin\thttps://github.com/GuilhermeLoscher/Movaura.git (push)\n",
      "stderr": ""
    },
    "log": {
      "argv": [
        "git",
        "log",
        "-10",
        "--oneline"
      ],
      "returncode": 0,
      "stdout": "ad18ee5 Prepare license compliance audit package\ncab576b Merge pull request #1 from GuilhermeLoscher/migration/pyside6\nadb43f5 Document final PR CI validation\n70f6ec9 Fix CI MSIX checksum generation\nba53689 Pin Pillow for MSIX asset generation\n1251e50 Make smoke tests independent of bundled wallpapers\na382c10 Record PR CI validation blocker\n89709fb Document CI and PR validation plan\n7a13b22 Finalize Store audit evidence\n7793d42 Harden Store audit docs and package safety\n",
      "stderr": ""
    },
    "diff_check": {
      "argv": [
        "git",
        "diff",
        "--check"
      ],
      "returncode": 2,
      "stdout": "docs/LICENSE_COMPLIANCE_TEST_REPORT.md:120: new blank line at EOF.\nlicenses/pillow/LICENSE:665: trailing whitespace.\n+a copy of this software and associated documentation files (the \nlicenses/pillow/LICENSE:668: trailing whitespace.\n+distribute, sublicense, and/or sell copies of the Software, and to \nlicenses/pillow/LICENSE:672: trailing whitespace.\n+The above copyright notice and this permission notice shall be \nlicenses/
```

## audit_qt_modules

```json
{
  "argv": [
    "C:\\NovaWall\\.build-venv\\Scripts\\python.exe",
    "C:\\NovaWall\\Movaura\\scripts\\audit_qt_modules.py"
  ],
  "returncode": 0,
  "stdout": "qt_records=187\n",
  "stderr": ""
}
```

## audit_python_licenses

```json
{
  "argv": [
    "C:\\NovaWall\\.build-venv\\Scripts\\python.exe",
    "C:\\NovaWall\\Movaura\\scripts\\audit_python_licenses.py"
  ],
  "returncode": 0,
  "stdout": "python_license_rows=13\n",
  "stderr": ""
}
```

## audit_ffmpeg_compliance

```json
{
  "argv": [
    "C:\\NovaWall\\.build-venv\\Scripts\\python.exe",
    "C:\\NovaWall\\Movaura\\scripts\\audit_ffmpeg_compliance.py"
  ],
  "returncode": 0,
  "stdout": "",
  "stderr": ""
}
```
