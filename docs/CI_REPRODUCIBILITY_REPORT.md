# CI reproducibility report

Date: 2026-07-23

Branch: `migration/pyside6`

Commit: `7a13b2266a531b431984b1b219175c6b2233ab2e`

Status: `READY FOR CI REVIEW`

## Dependency lock

The GitHub Actions workflow installs build dependencies from `requirements-build.txt`.

Pinned dependencies:

| Package | Version | Reason |
| --- | --- | --- |
| PySide6 | 6.10.0 | Qt runtime used by the application after PyQt6 migration. |
| PySide6_Addons | 6.10.0 | Qt add-on modules required by packaged PySide6. |
| PySide6_Essentials | 6.10.0 | Core Qt modules required by packaged PySide6. |
| shiboken6 | 6.10.0 | PySide6 binding runtime. |
| pywin32 | 311 | Windows desktop, Explorer, tray and native integration helpers. |
| pyinstaller | 6.20.0 | Standalone packaging tool. |
| pyinstaller-hooks-contrib | 2026.5 | PyInstaller hook set used during packaging. |
| altgraph | 0.17.5 | PyInstaller dependency. |
| packaging | 25.0 | Packaging/version helper dependency. |
| pefile | 2024.8.26 | PyInstaller Windows binary analysis dependency. |
| pywin32-ctypes | 0.2.3 | PyInstaller Windows helper dependency. |

## Install command

```powershell
python -m pip install -r requirements-build.txt
```

## Workflow environment

- Runner: `windows-latest`
- Python: `3.12`
- Qt mode for tests: `QT_QPA_PLATFORM=offscreen`
- Bytecode writing disabled: `PYTHONDONTWRITEBYTECODE=1`

## Local versus GitHub Actions

Local validation was performed on the development machine with the Windows SDK and Windows App Certification Kit available. GitHub Actions validates build reproducibility, packaging, smoke tests and artifacts, but WACK is intentionally not run in CI because the runner environment is not guaranteed to support the Windows App Certification Kit correctly.

Local WACK evidence is preserved in `release/certification/wack-20260723-172615.xml`.

## Risks

- `requirements-build.txt` pins exact versions, but does not yet use hash-pinned installs.
- `windows-latest` may move to newer runner images over time.
- Binary package contents may differ slightly between local and CI builds due timestamps or bundled runtime differences.

## Next step

Open the pull request and verify the GitHub Actions run for commit `7a13b2266a531b431984b1b219175c6b2233ab2e` or any later legitimate CI-fix commit.
